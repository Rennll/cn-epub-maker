from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol


class TransformationError(Exception):
    """Fatal error: the transformation cannot produce trustworthy output."""


@dataclass
class TransformResult:
    text: str
    changed: bool
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TransformAudit:
    """One successful transformation stage recorded by the pipeline."""

    name: str
    changed: bool
    warnings: list[str]
    stats: dict[str, Any]
    metadata: dict[str, Any]


class Transformer(Protocol):
    name: str

    def transform(self, text: str) -> TransformResult: ...


@dataclass(frozen=True)
class JunkRule:
    target: str
    matcher: str
    pattern: str


class JunkCleaner:
    name = "junk_cleaner"

    def __init__(self, rules: list[JunkRule] | None = None) -> None:
        self.rules = rules or []

    def transform(self, text: str) -> TransformResult:
        current = text
        warnings: list[str] = []
        matched = 0
        per_rule: list[dict[str, Any]] = []
        for index, rule in enumerate(self.rules, start=1):
            if rule.target not in {"line", "block"} or rule.matcher not in {"exact", "contains", "regex"}:
                warnings.append(f"rule {index}: invalid target/matcher; rule skipped")
                per_rule.append({"rule": index, "matched": 0, "removed": 0})
                continue
            if rule.matcher == "regex":
                try:
                    re.compile(rule.pattern)
                except re.error as exc:
                    warnings.append(f"rule {index} regex {rule.pattern!r}: {exc}; rule skipped")
                    per_rule.append({"rule": index, "matched": 0, "removed": 0})
                    continue
            current, count, locations, removed_content = self._apply_rule(current, rule)
            matched += count
            per_rule.append(
                {
                    "rule": index,
                    "matched": count,
                    "removed": count,
                    "locations": locations,
                    "content": removed_content,
                }
            )
        canonical = "\n".join("" if line.strip() == "" else line for line in current.split("\n"))
        return TransformResult(
            text=canonical,
            changed=canonical != text,
            warnings=warnings,
            stats={"matched": matched, "removed": matched, "rules": len(self.rules), "per_rule": per_rule},
            metadata={"name": self.name},
        )

    @staticmethod
    def _apply_rule(
        text: str, rule: JunkRule
    ) -> tuple[str, int, tuple[int, ...], tuple[str, ...]]:
        lines = text.split("\n")
        if rule.target == "line":
            out: list[tuple[str, bool]] = []
            locations: list[int] = []
            removed_content: list[str] = []
            for number, line in enumerate(lines, 1):
                if _matches(line, rule.matcher, rule.pattern):
                    locations.append(number)
                    removed_content.append(line)
                    out.append(("", True))
                else:
                    out.append((line, False))
            return (
                JunkCleaner._cleanup_removed_blank_runs(out),
                len(locations),
                tuple(locations),
                tuple(removed_content),
            )

        out: list[tuple[str, bool]] = []
        locations: list[int] = []
        removed_content: list[str] = []
        block_index = 0
        i = 0
        while i < len(lines):
            if lines[i].strip() == "":
                out.append((lines[i], False))
                i += 1
                continue
            start = i
            while i < len(lines) and lines[i].strip() != "":
                i += 1
            block = lines[start:i]
            if _matches("\n".join(block), rule.matcher, rule.pattern):
                locations.append(block_index)
                removed_content.append("\n".join(block))
                # Collapsed removed block to a single marker for blank-run merging
                out.append(("", True))
            else:
                out.extend((line, False) for line in block)
            block_index += 1
        return (
            JunkCleaner._cleanup_removed_blank_runs(out),
            len(locations),
            tuple(locations),
            tuple(removed_content),
        )

    @staticmethod
    def _cleanup_removed_blank_runs(lines: list[tuple[str, bool]]) -> str:
        """Collapse blank runs joined by removed line/block markers."""
        out: list[str] = []
        i = 0
        while i < len(lines):
            if not lines[i][1] and lines[i][0].strip() != "":
                out.append(lines[i][0])
                i += 1
                continue

            start = i
            has_removed = False
            max_blank_run = 0
            blank_run = 0
            while i < len(lines) and (
                lines[i][1] or lines[i][0].strip() == ""
            ):
                removed = lines[i][1]
                if removed:
                    has_removed = True
                    max_blank_run = max(max_blank_run, blank_run)
                    blank_run = 0
                else:
                    blank_run += 1
                i += 1
            max_blank_run = max(max_blank_run, blank_run)

            if has_removed:
                out.extend([""] * max_blank_run)
            else:
                out.extend(lines[index][0] for index in range(start, i))

        return "\n".join(out)

def _matches(target: str, matcher: str, pattern: str) -> bool:
    if matcher == "exact":
        return target == pattern
    if matcher == "contains":
        return pattern in target
    return re.search(pattern, target) is not None


class OpenCCTransformer:
    """Convert source text with a registered OpenCC conversion profile."""

    name = "opencc"

    _PROFILES = {
        "s2twp": "s2twp.json",
        "s2t": "s2t.json",
    }

    def __init__(self, profile: str = "s2twp") -> None:
        self.profile = profile

    @classmethod
    def available_profiles(cls) -> tuple[str, ...]:
        return tuple(sorted(cls._PROFILES))

    def transform(self, text: str) -> TransformResult:
        config = self._PROFILES.get(self.profile)
        if config is None:
            raise TransformationError(f"invalid OpenCC profile: {self.profile}")

        try:
            from opencc import OpenCC
            converter = OpenCC(config)
            converted = converter.convert(text)
        except Exception as exc:
            raise TransformationError(
                f"OpenCC conversion failed for profile {self.profile!r}: {exc}"
            ) from exc

        return TransformResult(
            text=converted,
            changed=converted != text,
            metadata={"profile": self.profile},
        )


class PunctuationTransformer:
    """Normalize selected ASCII punctuation in Chinese text."""

    name = "punctuation"

    _DIRECT_MAP = str.maketrans({
        "“": "「",
        "”": "」",
        "‘": "『",
        "’": "』",
    })
    _CONTEXT_MAP = {
        ",": "，",
        "!": "！",
        "?": "？",
        ":": "：",
        ";": "；",
    }
    _URL_OR_EMAIL = re.compile(
        r"(?:https?://[^\s，。！？；：、]+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
    )

    @classmethod
    def _is_chinese(cls, char: str) -> bool:
        return any(
            start <= ord(char) <= end
            for start, end in (
                (0x3400, 0x4DBF),
                (0x4E00, 0x9FFF),
                (0xF900, 0xFAFF),
            )
        )

    @classmethod
    def _is_meaningful(cls, char: str) -> bool:
        return (char.isascii() and char.isalnum()) or cls._is_chinese(char)

    def transform(self, text: str) -> TransformResult:
        protected = {
            match.span(): match.group(0)
            for match in self._URL_OR_EMAIL.finditer(text)
        }
        converted: list[str] = []
        chinese_context = False
        i = 0

        while i < len(text):
            protected_text = next((value for (start, _), value in protected.items() if start == i), None)
            if protected_text is not None:
                converted.append(protected_text)
                i += len(protected_text)
                continue

            char = text[i]
            direct = char.translate(self._DIRECT_MAP)
            if direct != char:
                converted.append(direct)
                i += 1
                continue

            if char == ".":
                end = i
                while end < len(text) and text[end] == ".":
                    end += 1
                run_length = end - i
                if chinese_context and run_length >= 3:
                    converted.append("……")
                elif chinese_context and run_length == 1:
                    converted.append("。")
                else:
                    converted.append(text[i:end])
                i = end
                continue

            if chinese_context and char in self._CONTEXT_MAP:
                converted.append(self._CONTEXT_MAP[char])
            else:
                converted.append(char)

            if self._is_meaningful(char):
                chinese_context = self._is_chinese(char)
            i += 1

        result = "".join(converted)
        return TransformResult(text=result, changed=result != text)


class TransformPipeline:
    def __init__(self, transformers: list[Transformer]) -> None:
        self.transformers = transformers

    def run(self, text: str) -> tuple[str, list[TransformAudit]]:
        current = text
        audit: list[TransformAudit] = []
        for transformer in self.transformers:
            try:
                result = transformer.transform(current)
            except TransformationError as exc:
                raise TransformationError(f"{transformer.name}: {exc}") from exc
            audit.append(
                TransformAudit(
                    name=transformer.name,
                    changed=result.changed,
                    warnings=list(result.warnings),
                    stats=dict(result.stats),
                    metadata=dict(result.metadata),
                )
            )
            current = result.text
        return current, audit

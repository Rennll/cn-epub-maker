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
        removed = 0
        for index, rule in enumerate(self.rules, start=1):
            if rule.target not in {"line", "block"} or rule.matcher not in {"exact", "contains", "regex"}:
                warnings.append(f"rule {index}: invalid target/matcher; rule skipped")
                continue
            try:
                current, count = self._apply_rule(current, rule)
            except re.error as exc:
                warnings.append(f"rule {index} regex {rule.pattern!r}: {exc}; rule skipped")
                continue
            matched += count
            removed += count
        canonical = "\n".join("" if line.strip() == "" else line for line in current.split("\n"))
        return TransformResult(
            text=canonical,
            changed=canonical != text,
            warnings=warnings,
            stats={"matched": matched, "removed": removed, "rules": len(self.rules)},
            metadata={"name": self.name},
        )

    @staticmethod
    def _apply_rule(text: str, rule: JunkRule) -> tuple[str, int]:
        lines = text.split("\n")
        if rule.target == "line":
            out: list[str] = []
            count = 0
            for line in lines:
                if _matches(line, rule.matcher, rule.pattern):
                    count += 1
                else:
                    out.append(line)
            return "\n".join(out), count

        blocks = _split_blocks(lines)
        out_blocks: list[list[str]] = []
        count = 0
        for block in blocks:
            target = "\n".join(block)
            if _matches(target, rule.matcher, rule.pattern):
                count += 1
            else:
                out_blocks.append(block)
        return "\n\n".join("\n".join(block) for block in out_blocks), count


def _matches(target: str, matcher: str, pattern: str) -> bool:
    if matcher == "exact":
        return target == pattern
    if matcher == "contains":
        return pattern in target
    return re.search(pattern, target) is not None


def _split_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


class TransformPipeline:
    def __init__(self, transformers: list[Transformer]) -> None:
        self.transformers = transformers

    def run(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        current = text
        audit: list[dict[str, Any]] = []
        for transformer in self.transformers:
            result = transformer.transform(current)
            audit.append({
                "name": transformer.name,
                "changed": result.changed,
                "warnings": result.warnings,
                "stats": result.stats,
                "metadata": result.metadata,
            })
            if result.warnings:
                # Warnings are recoverable by contract; the affected operation already skipped itself.
                pass
            current = result.text
        return current, audit

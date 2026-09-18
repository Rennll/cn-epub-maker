"""Deterministic, read-only inspection helpers for JunkRule authoring."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .junk_rule_configuration import parse_junk_rule
from .physical import PhysicalDocument
from .transforms import JunkRule, _matches


_URL_PATTERN = re.compile(
    r"\[[^\]\n]*\]\(https?://[^\s)]+\)"
    r"|https?://[^\s]+"
    r"|(?:www\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?"
)
_ID_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_-]*[A-Za-z])(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{8,}(?![A-Za-z0-9_-])"
)
_VARIABLES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("url", _URL_PATTERN),
    ("date", re.compile(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{4}年\d{1,2}月\d{1,2}日")),
    ("time", re.compile(r"\d{1,2}:\d{2}(?::\d{2})?|\d{1,2}時\d{1,2}分")),
    ("id", _ID_PATTERN),
    ("number", re.compile(r"\d+")),
)
_VARIABLE_PRIORITY = {name: index for index, (name, _) in enumerate(_VARIABLES)}
_FORMAT_MARKER_PATTERN = re.compile(
    r"(?:字數|字数|頁數|页数|更新|發布|发布|來源|来源|作者|網址|网址|版本|日期|時間|时间)"
)


@dataclass(frozen=True)
class DetectionGroup:
    """A set of physical occurrences sharing a deterministic pattern."""

    scope: str
    pattern: str
    occurrences: tuple[int, ...]
    evidence: tuple[str, ...]
    suggested_rule: JunkRule | None
    qualified: bool = True

    def __post_init__(self) -> None:
        if self.qualified and self.suggested_rule is None:
            raise ValueError("qualified detection group requires a suggested JunkRule")
        if not self.qualified and self.suggested_rule is not None:
            raise ValueError("unqualified detection group cannot have a suggested JunkRule")


@dataclass(frozen=True)
class RulePreview:
    """Read-only matching results for a canonical JunkRule."""

    matched_count: int
    affected_block_count: int
    examples: tuple[str, ...]
    locations: tuple[int, ...]


def detect_document(document: PhysicalDocument) -> tuple[DetectionGroup, ...]:
    """Find deterministic repeated line and block candidates in a physical document."""
    groups = [*_detect_lines(document), *_detect_blocks(document)]
    return tuple(sorted(groups, key=_group_sort_key))


def preview_rule(document: PhysicalDocument, rule: JunkRule) -> RulePreview:
    """Validate and preview a JunkRule without changing the physical document."""
    canonical = parse_junk_rule(rule)
    if canonical.target == "line":
        return _preview_lines(document, canonical)
    if canonical.target == "block":
        return _preview_blocks(document, canonical)
    raise ValueError(f"invalid junk rule target: {canonical.target!r}")


def _preview_lines(document: PhysicalDocument, rule: JunkRule) -> RulePreview:
    matches = [line for line in document.lines if _matches(line.text, rule.matcher, rule.pattern)]
    block_by_line = {line_number: block.index for block in document.blocks for line_number in block.line_numbers}
    affected_blocks = {block_by_line[line.number] for line in matches if line.number in block_by_line}
    return RulePreview(
        len(matches),
        len(affected_blocks),
        tuple(line.text for line in matches[:5]),
        tuple(line.number for line in matches),
    )


def _preview_blocks(document: PhysicalDocument, rule: JunkRule) -> RulePreview:
    lines_by_number = {line.number: line.text for line in document.lines}
    blocks = [
        (block.index, "\n".join(lines_by_number[number] for number in block.line_numbers))
        for block in document.blocks
    ]
    matches = [(index, text) for index, text in blocks if _matches(text, rule.matcher, rule.pattern)]
    return RulePreview(
        len(matches),
        len(matches),
        tuple(text for _, text in matches[:5]),
        tuple(index + 1 for index, _ in matches),
    )


def _detect_lines(document: PhysicalDocument) -> list[DetectionGroup]:
    exact: dict[str, list[int]] = {}
    patterned: dict[tuple[tuple[str, ...], str], list[int]] = {}
    pattern_values: dict[tuple[tuple[str, ...], str], list[str]] = {}
    for line in document.lines:
        if line.blank:
            continue
        exact.setdefault(line.text, []).append(line.number)
        candidate = _deterministic_pattern(line.text)
        if candidate is None:
            continue
        pattern, families, _ = candidate
        key = (families, pattern)
        patterned.setdefault(key, []).append(line.number)
        pattern_values.setdefault(key, []).append(line.text)
    return _make_groups("line", exact, patterned, pattern_values)


def _detect_blocks(document: PhysicalDocument) -> list[DetectionGroup]:
    exact: dict[str, list[int]] = {}
    patterned: dict[tuple[tuple[str, ...], str], list[int]] = {}
    pattern_values: dict[tuple[tuple[str, ...], str], list[str]] = {}
    lines_by_number = {line.number: line.text for line in document.lines}
    for block in document.blocks:
        text = "\n".join(lines_by_number[number] for number in block.line_numbers)
        # DetectionGroup exposes user-facing 1-based block locations, while
        # PhysicalBlock.index remains an internal 0-based index.
        exact.setdefault(text, []).append(block.index + 1)
        candidate = _deterministic_pattern(text)
        if candidate is None:
            continue
        pattern, families, _ = candidate
        key = (families, pattern)
        patterned.setdefault(key, []).append(block.index + 1)
        pattern_values.setdefault(key, []).append(text)
    return _make_groups("block", exact, patterned, pattern_values)


def _make_groups(
    scope: str,
    exact: dict[str, list[int]],
    patterned: dict[tuple[tuple[str, ...], str], list[int]],
    pattern_values: dict[tuple[tuple[str, ...], str], list[str]],
) -> list[DetectionGroup]:
    groups: list[DetectionGroup] = []
    for text, occurrences in exact.items():
        if len(occurrences) >= 2:
            groups.append(_make_group(scope, text, occurrences, ("repetition",), JunkRule(scope, "exact", text), True))
    for (families, pattern), occurrences in patterned.items():
        values = pattern_values[(families, pattern)]
        if len(occurrences) < 2 or len(set(values)) < 2:
            continue
        format_evidence = _has_format_evidence(families, pattern, values)
        evidence = ("repetition", "pattern", "format") if format_evidence else ("repetition", "pattern")
        qualified = "number" not in families or format_evidence
        rule = JunkRule(scope, "regex", _pattern_to_regex(pattern)) if qualified else None
        groups.append(_make_group(scope, pattern, occurrences, evidence, rule, qualified))
    return groups


def _has_format_evidence(
    families: tuple[str, ...],
    pattern: str,
    values: list[str],
) -> bool:
    """Return true only when each variable family has concrete format evidence."""
    if not values:
        return False

    if "number" in families and not _FORMAT_MARKER_PATTERN.search(pattern):
        return False

    for family in families:
        if family == "number":
            continue
        expression = dict(_VARIABLES)[family]
        observed = [match.group(0) for value in values for match in expression.finditer(value)]
        if not observed or not all(_observed_variable_has_format(family, value) for value in observed):
            return False
    return True


def _observed_variable_has_format(family: str, value: str) -> bool:
    """Check the observed values themselves, rather than inferring from family name."""
    if family == "url":
        return bool(re.search(r"(?:https?://|www\.)", value) or value.startswith("["))
    if family == "date":
        return bool(re.search(r"[-/]\d|年\d|\d日$", value))
    if family == "time":
        return bool(re.search(r":|時\d{1,2}分", value))
    if family == "id":
        return bool(re.search(r"[A-Za-z]", value) and re.search(r"\d", value))
    return False


def _deterministic_pattern(
    text: str,
) -> tuple[str, tuple[str, ...], tuple[str, ...]] | None:
    """Abstract every non-overlapping supported variable in one deterministic pass."""
    matches: list[tuple[int, int, str, str]] = []
    cursor = 0
    while cursor < len(text):
        best: tuple[int, int, str, str] | None = None
        for family, expression in _VARIABLES:
            match = expression.search(text, cursor)
            if match is None:
                continue
            candidate = (match.start(), match.end(), family, match.group(0))
            if best is None or (candidate[0], _variable_priority(candidate[2])) < (
                best[0],
                _variable_priority(best[2]),
            ):
                best = candidate
        if best is None:
            break
        matches.append(best)
        cursor = best[1]

    if not matches:
        return None

    pieces: list[str] = []
    values: list[str] = []
    families: list[str] = []
    cursor = 0
    for start, end, family, value in matches:
        pieces.extend((text[cursor:start], f"<{family}>"))
        values.append(value)
        if family not in families:
            families.append(family)
        cursor = end
    pieces.append(text[cursor:])
    pattern = "".join(pieces)
    if "url" in families:
        # Keep the historical URL candidate spelling stable: full-width
        # Chinese colon is canonicalized to ASCII in the human-readable pattern.
        pattern = pattern.replace("：<url>", ":<url>")
    return pattern, tuple(families), tuple(values)


def _variable_priority(family: str) -> int:
    return _VARIABLE_PRIORITY[family]


def _pattern_to_regex(pattern: str) -> str:
    variable_regex = {
        "number": r"\d+",
        "url": r"(?:\[[^\]\n]*\]\(https?://[^\s)]+\)|https?://[^\s]+|www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?)",
        "date": r"(?:\d{4}(?:[-/]\d{1,2}[-/]\d{1,2}|年\d{1,2}月\d{1,2}日))",
        "time": r"(?:\d{1,2}:\d{2}(?::\d{2})?|\d{1,2}時\d{1,2}分)",
        "id": r"(?=[A-Za-z0-9_-]*[A-Za-z])(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{8,}",
    }
    placeholder = re.compile(r"<(number|url|date|time|id)>")
    parts, cursor = [], 0
    for match in placeholder.finditer(pattern):
        literal = pattern[cursor:match.start()]
        parts.append(re.escape(literal))
        parts.append(variable_regex[match.group(1)])
        cursor = match.end()
    parts.append(re.escape(pattern[cursor:]))
    primary = "^" + "".join(parts) + "$"
    if "：" not in pattern and ":" in pattern:
        # Detection canonicalizes a full-width Chinese colon to ASCII for the
        # human-readable pattern. Keep the suggested rule readable while making
        # the executable regex match both source spellings.
        alternate = pattern.replace(":", "：", 1)
        return primary + "|" + _pattern_to_regex(alternate)
    return primary


def _make_group(
    scope: str,
    pattern: str,
    occurrences: list[int],
    evidence: tuple[str, ...],
    rule: JunkRule | None,
    qualified: bool,
) -> DetectionGroup:
    return DetectionGroup(scope, pattern, tuple(occurrences), evidence, rule, qualified)


def _group_sort_key(group: DetectionGroup) -> tuple[int, int, str]:
    return (group.occurrences[0], 0 if group.scope == "line" else 1, group.pattern)

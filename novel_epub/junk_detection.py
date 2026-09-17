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
_VARIABLES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("url", _URL_PATTERN, "format"),
    ("date", re.compile(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{4}年\d{1,2}月\d{1,2}日"), "format"),
    ("time", re.compile(r"\d{1,2}:\d{2}(?::\d{2})?|\d{1,2}時\d{1,2}分"), "format"),
    ("id", re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9_-]*\d[A-Za-z0-9_-]{7,}(?![A-Za-z0-9])"), "format"),
    ("number", re.compile(r"\d+"), "pattern"),
)


@dataclass(frozen=True)
class DetectionGroup:
    """A set of physical occurrences sharing a deterministic pattern."""

    scope: str
    pattern: str
    occurrences: tuple[int, ...]
    evidence: tuple[str, ...]
    suggested_rule: JunkRule


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
        tuple(index for index, _ in matches),
    )


def _detect_lines(document: PhysicalDocument) -> list[DetectionGroup]:
    exact: dict[str, list[int]] = {}
    patterned: dict[tuple[str, str], list[int]] = {}
    pattern_values: dict[tuple[str, str], list[str]] = {}
    for line in document.lines:
        if line.blank:
            continue
        exact.setdefault(line.text, []).append(line.number)
        candidate = _deterministic_pattern(line.text)
        if candidate is None:
            continue
        pattern, family, _ = candidate
        key = (family, pattern)
        patterned.setdefault(key, []).append(line.number)
        pattern_values.setdefault(key, []).append(line.text)
    return _make_groups("line", exact, patterned, pattern_values)


def _detect_blocks(document: PhysicalDocument) -> list[DetectionGroup]:
    exact: dict[str, list[int]] = {}
    patterned: dict[tuple[str, str], list[int]] = {}
    pattern_values: dict[tuple[str, str], list[str]] = {}
    lines_by_number = {line.number: line.text for line in document.lines}
    for block in document.blocks:
        text = "\n".join(lines_by_number[number] for number in block.line_numbers)
        exact.setdefault(text, []).append(block.index)
        candidate = _deterministic_pattern(text)
        if candidate is None:
            continue
        pattern, family, _ = candidate
        key = (family, pattern)
        patterned.setdefault(key, []).append(block.index)
        pattern_values.setdefault(key, []).append(text)
    return _make_groups("block", exact, patterned, pattern_values)


def _make_groups(scope, exact, patterned, pattern_values):
    groups = []
    for text, occurrences in exact.items():
        if len(occurrences) >= 2:
            groups.append(_make_group(scope, text, occurrences, ("repetition",), JunkRule(scope, "exact", text)))
    for (family, pattern), occurrences in patterned.items():
        values = pattern_values[(family, pattern)]
        if len(occurrences) < 2 or len(set(values)) < 2:
            continue
        evidence = ("repetition", "pattern", "format") if family != "number" else ("repetition", "pattern")
        groups.append(
            _make_group(
                scope,
                pattern,
                occurrences,
                evidence,
                JunkRule(scope, "regex", _pattern_to_regex(pattern)),
            )
        )
    return groups


def _deterministic_pattern(text: str):
    for family, expression, _ in _VARIABLES:
        matches = tuple(expression.finditer(text))
        if not matches:
            continue
        pieces, values, cursor = [], [], 0
        for match in matches:
            pieces.extend((text[cursor:match.start()], f"<{family}>"))
            values.append(match.group(0))
            cursor = match.end()
        pieces.append(text[cursor:])
        return "".join(pieces), family, tuple(values)
    return None


def _pattern_to_regex(pattern: str) -> str:
    variable_regex = {
        "number": r"\d+",
        "url": r"\[[^\]\n]*\]\(https?://[^\s)]+\)|https?://[^\s]+|www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?",
        "date": r"\d{4}(?:[-/]\d{1,2}[-/]\d{1,2}|年\d{1,2}月\d{1,2}日)",
        "time": r"(?:\d{1,2}:\d{2}(?::\d{2})?|\d{1,2}時\d{1,2}分)",
        "id": r"[A-Za-z0-9_-]*\d[A-Za-z0-9_-]{7,}",
    }
    placeholder = re.compile(r"<(number|url|date|time|id)>")
    parts, cursor = [], 0
    for match in placeholder.finditer(pattern):
        parts.append(re.escape(pattern[cursor:match.start()]))
        parts.append(variable_regex[match.group(1)])
        cursor = match.end()
    parts.append(re.escape(pattern[cursor:]))
    return "^" + "".join(parts) + "$"


def _make_group(scope, pattern, occurrences, evidence, rule):
    return DetectionGroup(scope, pattern, tuple(occurrences), evidence, rule)


def _group_sort_key(group):
    return (group.occurrences[0], 0 if group.scope == "line" else 1, group.pattern)

"""Deterministic, read-only inspection helpers for JunkRule authoring."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .physical import PhysicalDocument
from .transforms import JunkRule


_NUMBER_RE = re.compile(r"\d+")


@dataclass(frozen=True)
class DetectionGroup:
    """A set of physical occurrences sharing a deterministic pattern."""

    scope: str
    pattern: str
    occurrences: tuple[int, ...]
    evidence: tuple[str, ...]
    suggested_rule: JunkRule


def detect_document(document: PhysicalDocument) -> tuple[DetectionGroup, ...]:
    """Find deterministic repeated line and block candidates in a physical document."""
    groups = [*_detect_lines(document), *_detect_blocks(document)]
    return tuple(sorted(groups, key=_group_sort_key))


def _detect_lines(document: PhysicalDocument) -> list[DetectionGroup]:
    groups: list[DetectionGroup] = []
    exact: dict[str, list[int]] = {}
    patterned: dict[str, list[int]] = {}
    pattern_values: dict[str, list[str]] = {}

    for line in document.lines:
        if line.blank:
            continue
        exact.setdefault(line.text, []).append(line.number)
        pattern = _number_pattern(line.text)
        if pattern is not None:
            patterned.setdefault(pattern[0], []).append(line.number)
            pattern_values.setdefault(pattern[0], []).append(line.text)

    for text, occurrences in exact.items():
        if len(occurrences) < 2:
            continue
        groups.append(
            _make_group(
                scope="line",
                pattern=text,
                occurrences=occurrences,
                evidence=("repetition",),
                rule=JunkRule("line", "exact", text),
            )
        )

    for pattern, occurrences in patterned.items():
        values = pattern_values[pattern]
        if len(occurrences) < 2 or len(set(values)) < 2:
            continue
        groups.append(
            _make_group(
                scope="line",
                pattern=pattern,
                occurrences=occurrences,
                evidence=("repetition", "pattern"),
                rule=JunkRule("line", "regex", _pattern_to_regex(pattern)),
            )
        )

    return groups


def _detect_blocks(document: PhysicalDocument) -> list[DetectionGroup]:
    groups: list[DetectionGroup] = []
    exact: dict[str, list[int]] = {}
    patterned: dict[str, list[int]] = {}
    pattern_values: dict[str, list[str]] = {}

    lines_by_number = {line.number: line.text for line in document.lines}
    for block in document.blocks:
        text = "\n".join(lines_by_number[number] for number in block.line_numbers)
        exact.setdefault(text, []).append(block.index)
        pattern = _number_pattern(text)
        if pattern is not None:
            patterned.setdefault(pattern[0], []).append(block.index)
            pattern_values.setdefault(pattern[0], []).append(text)

    for text, occurrences in exact.items():
        if len(occurrences) < 2:
            continue
        groups.append(
            _make_group(
                scope="block",
                pattern=text,
                occurrences=occurrences,
                evidence=("repetition",),
                rule=JunkRule("block", "exact", text),
            )
        )

    for pattern, occurrences in patterned.items():
        values = pattern_values[pattern]
        if len(occurrences) < 2 or len(set(values)) < 2:
            continue
        groups.append(
            _make_group(
                scope="block",
                pattern=pattern,
                occurrences=occurrences,
                evidence=("repetition", "pattern"),
                rule=JunkRule("block", "regex", _pattern_to_regex(pattern)),
            )
        )

    return groups


def _number_pattern(text: str) -> tuple[str, tuple[str, ...]] | None:
    matches = tuple(_NUMBER_RE.finditer(text))
    if not matches:
        return None
    pieces: list[str] = []
    cursor = 0
    for match in matches:
        pieces.append(text[cursor : match.start()])
        pieces.append("<number>")
        cursor = match.end()
    pieces.append(text[cursor:])
    pattern = "".join(pieces)
    return pattern, tuple(match.group(0) for match in matches)


def _pattern_to_regex(pattern: str) -> str:
    parts: list[str] = []
    cursor = 0
    for match in re.finditer(r"<number>", pattern):
        parts.append(re.escape(pattern[cursor : match.start()]))
        parts.append(r"\d+")
        cursor = match.end()
    parts.append(re.escape(pattern[cursor:]))
    return "^" + "".join(parts) + "$"


def _make_group(
    *,
    scope: str,
    pattern: str,
    occurrences: list[int],
    evidence: tuple[str, ...],
    rule: JunkRule,
) -> DetectionGroup:
    return DetectionGroup(
        scope=scope,
        pattern=pattern,
        occurrences=tuple(occurrences),
        evidence=evidence,
        suggested_rule=rule,
    )


def _group_sort_key(group: DetectionGroup) -> tuple[int, int, str]:
    return (group.occurrences[0], 0 if group.scope == "line" else 1, group.pattern)

from novel_epub.junk_detection import detect_document
from novel_epub.physical import build_physical_document


def test_repeated_line_becomes_detection_group_with_exact_rule():
    document = build_physical_document(
        [
            "第一章",
            "本章字數：1234",
            "正文",
            "本章字數：5678",
            "下一章",
        ]
    )

    groups = detect_document(document)

    assert len(groups) == 1
    group = groups[0]
    assert group.scope == "line"
    assert group.pattern == "本章字數：<number>"
    assert group.occurrences == (2, 4)
    assert group.qualified is True
    assert group.suggested_rule is not None
    assert group.suggested_rule.target == "line"
    assert group.suggested_rule.matcher == "regex"
    assert group.suggested_rule.pattern == r"^本章字數：\d+$"
    assert "repetition" in group.evidence
    assert "pattern" in group.evidence
    assert "format" in group.evidence


def test_repeated_numbered_headings_are_detected_but_not_qualified():
    document = build_physical_document(
        [
            "第一章",
            "第1章",
            "正文",
            "第2章",
            "第3章",
            "結尾",
        ]
    )

    groups = detect_document(document)

    numeric_groups = [group for group in groups if group.pattern == "第<number>章"]
    assert len(numeric_groups) == 1
    group = numeric_groups[0]
    assert group.qualified is False
    assert group.suggested_rule is None
    assert group.evidence == ("repetition", "pattern")


def test_generic_numeric_pattern_without_format_marker_is_not_qualified():
    document = build_physical_document(["100", "正文", "200", "300"])

    groups = detect_document(document)

    numeric_groups = [group for group in groups if group.pattern == "<number>"]
    assert len(numeric_groups) == 1
    assert numeric_groups[0].qualified is False
    assert numeric_groups[0].suggested_rule is None


def test_identical_repeated_line_uses_exact_rule():
    document = build_physical_document(["正文", "本章完", "其他", "本章完"])

    groups = detect_document(document)

    assert len(groups) == 1
    assert groups[0].pattern == "本章完"
    assert groups[0].suggested_rule.target == "line"
    assert groups[0].suggested_rule.matcher == "exact"
    assert groups[0].suggested_rule.pattern == "本章完"


def test_single_occurrence_is_not_a_detection_group():
    document = build_physical_document(["正文", "本章字數：1234", "其他"])

    assert detect_document(document) == ()


def test_repeated_identical_blocks_produce_a_block_candidate():
    document = build_physical_document(["A", "B", "", "A", "B"])

    groups = detect_document(document)

    block_groups = [group for group in groups if group.scope == "block"]
    assert len(block_groups) == 1
    group = block_groups[0]
    assert group.occurrences == (0, 1)
    assert group.suggested_rule.target == "block"
    assert group.suggested_rule.matcher == "exact"
    assert group.suggested_rule.pattern == "A\nB"

from novel_epub.junk_detection import detect_document
from novel_epub.physical import build_physical_document


def test_multi_variable_number_still_requires_format_marker():
    groups = detect_document(build_physical_document(["章 1 2026-09-18", "章 2 2026-09-19"]))
    group = next(group for group in groups if group.pattern == "章 <number> <date>")
    assert group.qualified is False
    assert group.suggested_rule is None


def test_repeated_line_with_date_and_time_uses_both_variables():
    document = build_physical_document(["更新時間：2026-09-18 21:34", "正文", "更新時間：2026-09-19 08:12"])
    group = next(group for group in detect_document(document) if group.pattern == "更新時間：<date> <time>")
    assert group.occurrences == (1, 3)
    assert group.qualified is True
    assert group.suggested_rule is not None
    assert group.suggested_rule.pattern == (
        r"^更新時間：(?:\d{4}(?:[-/]\d{1,2}[-/]\d{1,2}|年\d{1,2}月\d{1,2}日)"
        r")\ (?:\d{1,2}:\d{2}(?::\d{2})?|\d{1,2}時\d{1,2}分)$"
    )


def test_repeated_block_with_date_and_time_uses_both_variables():
    groups = detect_document(build_physical_document(["更新時間：2026-09-18 21:34", "", "更新時間：2026-09-19 08:12"]))
    group = next(group for group in groups if group.scope == "block" and group.pattern == "更新時間：<date> <time>")
    assert group.occurrences == (0, 1)
    assert group.qualified is True


def test_multi_variable_pattern_keeps_literal_skeleton_anchored():
    document = build_physical_document(["更新時間：2026-09-18 21:34", "更新時間：2026-09-19 08:12", "更新時間：2026-09-20 17:45 extra"])
    group = next(group for group in detect_document(document) if group.pattern == "更新時間：<date> <time>")
    assert group.occurrences == (1, 2)
    assert group.suggested_rule.pattern.startswith("^")
    assert group.suggested_rule.pattern.endswith("$")


def test_multi_variable_number_still_requires_format_marker():
    groups = detect_document(build_physical_document(["章 1 2026-09-18", "章 2 2026-09-19"]))
    group = next(group for group in groups if group.pattern == "章 <number> <date>")
    assert group.qualified is False
    assert group.suggested_rule is None

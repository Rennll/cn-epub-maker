from novel_epub.junk_detection import detect_document
from novel_epub.physical import build_physical_document


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

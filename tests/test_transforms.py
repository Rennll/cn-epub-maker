from novel_epub.transforms import JunkCleaner, JunkRule


def test_line_exact_removes_whole_line_and_canonicalizes_blank_whitespace():
    result = JunkCleaner([JunkRule("line", "exact", "ADVERTISEMENT")]).transform(
        "第一段\nADVERTISEMENT\n  \t\n第二段"
    )
    assert result.text == "第一段\n\n第二段"
    assert result.changed
    assert result.stats["matched"] == 1


def test_contains_removes_whole_target_not_substring():
    result = JunkCleaner([JunkRule("line", "contains", "廣告")]).transform(
        "保留廣告內容\n正常"
    )
    assert result.text == "正常"
    assert result.stats["removed"] == 1


def test_block_exact_uses_continuous_nonblank_lines():
    result = JunkCleaner([JunkRule("block", "exact", "A\nB")]).transform(
        "A\nB\n\nC\nD"
    )
    assert result.text == "\n\nC\nD"


def test_invalid_regex_is_warning_and_later_rule_runs():
    result = JunkCleaner([
        JunkRule("line", "regex", "["),
        JunkRule("line", "exact", "REMOVE"),
    ]).transform("REMOVE\nKEEP")
    assert result.text == "KEEP"
    assert len(result.warnings) == 1
    assert "rule 1" in result.warnings[0]


def test_rules_are_sequential():
    result = JunkCleaner([
        JunkRule("line", "contains", "A"),
        JunkRule("line", "exact", "B"),
    ]).transform("A\nB\nC")
    assert result.text == "C"

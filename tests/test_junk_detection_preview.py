from novel_epub.junk_detection import preview_rule
from novel_epub.physical import build_physical_document
from novel_epub.transforms import JunkRule


def test_preview_line_rule_reports_matches_blocks_examples_and_locations():
    document = build_physical_document(
        [
            "第一章",
            "本章字數：1234",
            "正文",
            "本章字數：5678",
            "下一章",
        ]
    )

    preview = preview_rule(
        document,
        JunkRule("line", "regex", r"^本章字數：\d+$"),
    )

    assert preview.matched_count == 2
    assert preview.affected_block_count == 1
    assert preview.examples == ("本章字數：1234", "本章字數：5678")
    assert preview.locations == (2, 4)


def test_preview_block_rule_uses_physical_block_boundaries():
    document = build_physical_document(["A", "B", "", "A", "C"])

    preview = preview_rule(document, JunkRule("block", "exact", "A\nB"))

    assert preview.matched_count == 1
    assert preview.affected_block_count == 1
    assert preview.examples == ("A\nB",)
    assert preview.locations == (0,)


def test_preview_contains_and_regex_follow_junk_cleaner_matching_semantics():
    document = build_physical_document(["章節字數：100", "正文", "章節字數：200"])

    contains_preview = preview_rule(
        document,
        JunkRule("line", "contains", "字數"),
    )
    regex_preview = preview_rule(
        document,
        JunkRule("line", "regex", r"章節字數：\d+"),
    )

    assert contains_preview.locations == (1, 3)
    assert regex_preview.locations == (1, 3)


def test_preview_is_read_only():
    lines = ["A", "本章字數：1234", "", "B"]
    document = build_physical_document(lines)

    preview_rule(document, JunkRule("line", "regex", r"^本章字數：\d+$"))

    assert [line.text for line in document.lines] == lines
    assert document.blocks[0].line_numbers == (1, 2)
    assert document.blank_runs[0].line_numbers == (3,)

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
    assert group.suggested_rule.target == "line"
    assert group.suggested_rule.matcher == "regex"
    assert group.suggested_rule.pattern == r"^本章字數：\d+$"
    assert "repetition" in group.evidence
    assert "pattern" in group.evidence


def test_identical_repeated_line_uses_exact_rule():
    document = build_physical_document(
        ["正文", "本章完", "其他", "本章完"]
    )

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

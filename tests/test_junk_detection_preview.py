from novel_epub.junk_detection import preview_rule
from novel_epub.physical import build_physical_document
from novel_epub.transforms import JunkCleaner, JunkRule


def _cleaner_details(document, rule):
    source = "\n".join(line.text for line in document.lines)
    result = JunkCleaner([rule]).transform(source)
    detail = result.stats["per_rule"][0]
    return result, detail


def test_preview_matches_cleaner_line_exact_contains_regex():
    document = build_physical_document(
        ["廣告A", "正文", "廣告B", "正文"]
    )

    for rule in (
        JunkRule("line", "exact", "正文"),
        JunkRule("line", "contains", "廣告"),
        JunkRule("line", "regex", r"^廣告[AB]$"),
    ):
        preview = preview_rule(document, rule)
        result, detail = _cleaner_details(document, rule)

        assert preview.matched_count == result.stats["removed"]
        assert preview.locations == detail["locations"]
        assert preview.examples == detail["content"]
        assert [line.text for line in document.lines] == ["廣告A", "正文", "廣告B", "正文"]


def test_preview_matches_cleaner_block_rules():
    document = build_physical_document(
        ["廣告", "內容", "", "正文", "段落", "", "廣告", "內容"]
    )
    rule = JunkRule("block", "exact", "廣告\n內容")

    preview = preview_rule(document, rule)
    result, detail = _cleaner_details(document, rule)

    assert preview.matched_count == result.stats["removed"]
    assert preview.locations == detail["locations"] == (1, 3)
    assert preview.examples == detail["content"] == ("廣告\n內容", "廣告\n內容")
    assert [line.text for line in document.lines] == [
        "廣告", "內容", "", "正文", "段落", "", "廣告", "內容"
    ]


@pytest.mark.parametrize(
    "matcher, pattern",
    [
        ("contains", "廣告"),
        ("regex", r"^廣告\\n內容$"),
    ],
)
def test_preview_matches_cleaner_block_contains_and_regex(matcher, pattern):
    document = build_physical_document(
        ["廣告A", "內容", "", "正文", "段落", "", "廣告B", "內容"]
    )
    rule = JunkRule("block", matcher, pattern)

    preview = preview_rule(document, rule)
    result, detail = _cleaner_details(document, rule)

    assert preview.matched_count == result.stats["removed"]
    assert preview.locations == detail["locations"] == (1, 3)
    assert preview.examples == detail["content"] == ("廣告A\n內容", "廣告B\n內容")


def test_preview_matches_cleaner_url_forms():
    document = build_physical_document(
        [
            "https://example.com/raw",
            "www.example.com/path",
            "[官方網站](https://example.com/docs)",
            "保留內容",
        ]
    )

    for pattern in (
        "https://example.com/raw",
        "www.example.com/path",
        "[官方網站](https://example.com/docs)",
    ):
        rule = JunkRule("line", "exact", pattern)
        preview = preview_rule(document, rule)
        result, detail = _cleaner_details(document, rule)

        assert preview.locations == detail["locations"]
        assert preview.examples == detail["content"]
        assert preview.matched_count == result.stats["removed"]


def test_preview_matches_cleaner_no_match_and_adjacent_matches():
    document = build_physical_document(
        ["廣告", "廣告", "正文", "廣告"]
    )

    no_match = JunkRule("line", "exact", "不存在")
    preview = preview_rule(document, no_match)
    result, detail = _cleaner_details(document, no_match)
    assert preview.matched_count == 0
    assert preview.locations == ()
    assert detail["locations"] == ()
    assert detail["content"] == ()
    assert result.stats["removed"] == 0

    adjacent = JunkRule("line", "contains", "廣告")
    preview = preview_rule(document, adjacent)
    result, detail = _cleaner_details(document, adjacent)
    assert preview.locations == detail["locations"] == (1, 2, 4)
    assert preview.examples == detail["content"] == ("廣告", "廣告", "廣告")
    assert preview.matched_count == result.stats["removed"] == 3


def test_preview_does_not_mutate_cleaner_input():
    lines = ["廣告", "正文", "", "廣告", "內容"]
    document = build_physical_document(lines)
    before = document

    preview_rule(document, JunkRule("block", "exact", "廣告\n內容"))
    result, _ = _cleaner_details(document, JunkRule("line", "contains", "廣告"))

    assert document is before
    assert [line.text for line in document.lines] == lines
    assert result.stats["removed"] == 2

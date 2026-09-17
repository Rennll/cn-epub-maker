from novel_epub.junk_detection import detect_document
from novel_epub.physical import build_physical_document


def test_repeated_urls_share_url_pattern():
    document = build_physical_document(
        ["來源：https://example.com/a", "正文", "來源：https://example.com/b"]
    )
    groups = detect_document(document)
    group = next(group for group in groups if group.pattern.startswith("來源:<url>"))

    assert group.evidence == ("repetition", "pattern", "format")
    assert group.occurrences == (1, 3)
    assert group.suggested_rule.matcher == "regex"
    assert group.suggested_rule.pattern.startswith("^來源:")


def test_repeated_dates_share_date_pattern():
    document = build_physical_document(["更新：2026-09-01", "正文", "更新：2026-09-17"])
    groups = detect_document(document)
    group = next(group for group in groups if group.pattern == "更新：<date>")

    assert group.occurrences == (1, 3)
    assert group.suggested_rule.matcher == "regex"
    assert "\\d{4}" in group.suggested_rule.pattern


def test_repeated_times_share_time_pattern():
    document = build_physical_document(["發布時間 09:30", "正文", "發布時間 18:45"])
    groups = detect_document(document)
    group = next(group for group in groups if group.pattern == "發布時間 <time>")

    assert group.occurrences == (1, 3)
    assert group.suggested_rule.matcher == "regex"


def test_repeated_machine_ids_share_id_pattern():
    document = build_physical_document(["ID=abc12345", "正文", "ID=def67890"])
    groups = detect_document(document)
    group = next(group for group in groups if group.pattern == "ID=<id>")

    assert group.occurrences == (1, 3)
    assert group.evidence == ("repetition", "pattern", "format")


def test_single_number_family_does_not_create_pattern_without_repetition():
    document = build_physical_document(["章節 1234", "正文"])
    assert not detect_document(document)

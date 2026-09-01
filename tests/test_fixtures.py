from novel_epub.parser import parse_lines


def test_chapter_without_title_is_valid_and_duplicate_volume_is_warning():
    result = parse_lines([
        "第一卷 起点",
        "第1章",
        "第二卷 转折",
        "第1章 第二次第一章",
        "正文",
        "第二卷 重复卷号",
        "第2章 结束",
        "最后一段",
    ], title="书", author="作者")

    assert result.book.chapter_count == 3
    chapters = list(result.book.iter_chapters())
    assert chapters[0].title == ""
    assert not any(w.kind == "empty_chapter" for w in result.warnings)
    assert any(w.kind == "duplicate_chapter_number" for w in result.warnings)
    assert any(w.kind == "duplicate_volume_number" for w in result.warnings)


def test_special_xml_characters_are_preserved():
    text = '& < > " \' 原文'
    result = parse_lines(["第1章 特殊字符", text], title="书", author="作者")
    assert result.book.chapters[0].paragraphs[0].text == text


def test_last_line_without_newline_is_not_lost():
    result = parse_lines(["第1章 A", "最后一行"], title="书", author="作者")
    assert result.book.chapters[0].paragraphs[0].text == "最后一行"

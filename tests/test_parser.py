from novel_epub.parser import parse_lines


def test_two_volumes_and_original_numbers():
    result = parse_lines([
        "第一卷 九洲一号群",
        "第1章 黄山真君和九洲一号群",
        "　　2019年5月20日，星期一。",
        "",
        "　　春尽夏至。",
        "第二卷 武道筑基",
        "第26章 我那与众不同的炼丹炉",
        "　　平静的上完了最后一节课……",
    ], title="修真聊天群", author="圣骑士的传说")
    assert result.book.chapter_count == 2
    assert len(result.book.volumes) == 2
    assert result.book.volumes[0].number == "一"
    assert result.book.volumes[1].number == "二"
    chapters = list(result.book.iter_chapters())
    assert chapters[0].sequence == 1
    assert chapters[0].number == "1"
    assert chapters[0].label == "第1章"
    assert chapters[1].sequence == 2
    assert chapters[1].number == "26"
    assert chapters[1].label == "第26章"
    assert chapters[0].paragraphs[0].text.startswith("2019年5月20日")
    assert chapters[0].paragraphs[1].text == "春尽夏至。"


def test_no_volume_and_duplicate_number_warning():
    result = parse_lines([
        "第1章 A",
        "正文",
        "第3章 B",
        "正文",
        "第3章 C",
        "正文",
    ], title="书", author="作者")
    assert not result.book.volumes
    assert [c.number for c in result.book.chapters] == ["1", "3", "3"]
    assert any(w.kind == "duplicate_chapter_number" for w in result.warnings)


def test_preamble_is_warning_not_deleted():
    result = parse_lines([
        "书名简介",
        "作者：某人",
        "第一章可能是正文，但不是标准 heading",
        "第1章 真正的开始",
        "正文",
    ], title="书", author="作者")
    assert result.book.chapter_count == 1
    assert any(w.kind == "text_before_first_chapter" for w in result.warnings)

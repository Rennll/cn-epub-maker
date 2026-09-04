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
    assert chapters[0].number == 1
    assert chapters[0].label == "第1章"
    assert chapters[1].sequence == 2
    assert chapters[1].number == 26
    assert chapters[1].label == "第26章"
    assert chapters[0].paragraphs[0].text.startswith("2019年5月20日")
    assert chapters[0].paragraphs[1].text == "春尽夏至。"


def test_chinese_chapter_numbers_are_normalized():
    result = parse_lines([
        "第一章 開始",
        "第十章 十",
        "第一百章 百",
        "第一百零一章 一百零一",
        "第一千零二章 一千零二",
        "第一萬零三章 一萬零三",
    ], title="書", author="作者")

    chapters = list(result.book.iter_chapters())
    assert [chapter.number for chapter in chapters] == [1, 10, 100, 101, 1002, 10003]
    assert [chapter.label for chapter in chapters] == [
        "第一章", "第十章", "第一百章", "第一百零一章", "第一千零二章", "第一萬零三章"
    ]
    assert not any(w.kind == "unparsed_chapter_number" for w in result.warnings)


def test_chapter_number_may_be_spaced_and_chapter_may_have_no_title():
    result = parse_lines([
        "第 100 章",
        "正文",
        "第 一百零一 章",
        "正文",
    ], title="書", author="作者")

    chapters = list(result.book.iter_chapters())
    assert [chapter.number for chapter in chapters] == [100, 101]
    assert [chapter.title for chapter in chapters] == ["", ""]
    assert not any(w.kind == "empty_chapter" for w in result.warnings)


def test_chapter_title_may_touch_the_chapter_unit():
    result = parse_lines([
        "第1章殺豬美人",
        "正文A",
        "第 2 章落魄男人",
        "正文B",
    ], title="書", author="作者")

    chapters = list(result.book.iter_chapters())
    assert [(c.number, c.label, c.title) for c in chapters] == [
        (1, "第1章", "殺豬美人"),
        (2, "第 2 章", "落魄男人"),
    ]


def test_unparseable_chapter_number_is_not_forced_into_a_chapter():
    result = parse_lines([
        "第十百章 看起來像章節但格式不可靠",
        "第1章 真正開始",
        "正文",
    ], title="書", author="作者")

    chapters = list(result.book.iter_chapters())
    assert len(chapters) == 1
    assert chapters[0].number == 1
    assert any(w.kind == "unparsed_chapter_number" for w in result.warnings)


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
    assert [c.number for c in result.book.chapters] == [1, 3, 3]
    assert any(w.kind == "duplicate_chapter_number" for w in result.warnings)


def test_preamble_is_preserved_without_text_before_first_chapter_warning():
    result = parse_lines([
        "书名简介",
        "作者：某人",
        "这里是正式章节前的作品简介。",
        "第1章 真正的开始",
        "正文",
    ], title="书", author="作者")

    assert result.book.chapter_count == 1
    assert not any(w.kind == "text_before_first_chapter" for w in result.warnings)


def test_preamble_does_not_hide_a_real_chapter_header():
    result = parse_lines([
        "书名简介",
        "第1章 真正的开始",
        "正文",
    ], title="书", author="作者")

    chapters = list(result.book.iter_chapters())
    assert len(chapters) == 1
    assert chapters[0].number == 1
    assert chapters[0].paragraphs[0].text == "正文"
    assert not any(w.kind == "text_before_first_chapter" for w in result.warnings)


def test_extra_chapter_keeps_label_and_uses_sequence_not_chapter_number():
    result = parse_lines([
        "第100章 A",
        "正文A",
        "番外1",
        "番外正文",
        "第101章 B",
        "正文B",
    ], title="书", author="作者")

    chapters = list(result.book.iter_chapters())
    assert [(c.sequence, c.number, c.label, c.title) for c in chapters] == [
        (1, 100, "第100章", "A"),
        (2, None, "番外1", ""),
        (3, 101, "第101章", "B"),
    ]
    assert chapters[1].paragraphs[0].text == "番外正文"


def test_extra_chapter_inside_volume_preserves_toc_order():
    result = parse_lines([
        "第三卷",
        "第100章 A",
        "正文A",
        "番外1 初见",
        "番外正文",
        "第101章 B",
        "正文B",
    ], title="書", author="作者")

    volume = result.book.volumes[0]
    assert [(c.sequence, c.label) for c in volume.chapters] == [
        (1, "第100章"),
        (2, "番外1"),
        (3, "第101章"),
    ]
    assert [c.title for c in volume.chapters] == ["A", "初见", "B"]


def test_text_containing_extra_word_is_not_automatically_a_chapter():
    result = parse_lines([
        "第1章 A",
        "正文：這一段提到番外1，但不是標題。",
    ], title="書", author="作者")

    chapters = list(result.book.iter_chapters())
    assert len(chapters) == 1
    assert chapters[0].paragraphs[0].text == "正文：這一段提到番外1，但不是標題。"

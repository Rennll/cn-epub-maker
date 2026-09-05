import shutil
import zipfile
from pathlib import Path

import pytest

from novel_epub.normalize import read_lines
from novel_epub.parser import parse_lines
from novel_epub.renderers.pandoc import render


def test_one_line_web_novel_mode_splits_each_body_line():
    result = parse_lines(
        [
            "第1章 開始",
            "　　腊月的天飘着雪，院子里一口大锅正烧着热水……",
            "　　地上的积雪被踩化了，一片泥泞……",
            "　　锅炉旁边用板凳架起一张门板……",
        ],
        title="侯夫人与杀猪刀",
        author="某作者",
        paragraph_mode="line",
    )

    chapter = result.book.chapters[0]
    assert [p.text for p in chapter.paragraphs] == [
        "腊月的天飘着雪，院子里一口大锅正烧着热水……",
        "地上的积雪被踩化了，一片泥泞……",
        "锅炉旁边用板凳架起一张门板……",
    ]
    assert all("\n" not in p.text for p in chapter.paragraphs)


def test_wrapped_mode_remains_default_and_preserves_multiline_paragraphs():
    result = parse_lines(
        [
            "第1章 開始",
            "This is one logical paragraph",
            "that continues on the next physical line.",
            "",
            "This is the next paragraph.",
        ],
        title="書",
        author="作者",
    )

    assert [p.text for p in result.book.chapters[0].paragraphs] == [
        "This is one logical paragraph\nthat continues on the next physical line.",
        "This is the next paragraph.",
    ]


def test_line_mode_keeps_blank_lines_without_empty_paragraphs():
    result = parse_lines(
        ["第1章 開始", "第一段。", "", "第二段。"],
        title="書",
        author="作者",
        paragraph_mode="line",
    )

    chapter = result.book.chapters[0]
    assert [p.text for p in chapter.paragraphs] == ["第一段。", "第二段。"]
    assert all(p.text for p in chapter.paragraphs)


def test_line_mode_does_not_change_chapter_or_extra_heading_detection():
    result = parse_lines(
        [
            "第一卷",
            "第1章 A",
            "正文A",
            "正文B",
            "番外1 初見",
            "番外A",
            "番外B",
            "第2章 B",
            "正文C",
        ],
        title="書",
        author="作者",
        paragraph_mode="line",
    )

    volume = result.book.volumes[0]
    assert [(c.label, c.title) for c in volume.chapters] == [
        ("第1章", "A"),
        ("番外1", "初見"),
        ("第2章", "B"),
    ]
    assert [p.text for p in volume.chapters[0].paragraphs] == ["正文A", "正文B"]
    assert [p.text for p in volume.chapters[1].paragraphs] == ["番外A", "番外B"]
    assert [p.text for p in volume.chapters[2].paragraphs] == ["正文C"]


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_txt_to_epub_pipeline_produces_paragraph_level_xhtml(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第1章 開始\n"
        "　　第一個段落。\n"
        "　　第二個段落。\n"
        "　　第三個段落。\n",
        encoding="utf-8",
    )
    lines, encoding = read_lines(source, "utf-8")
    assert encoding == "utf-8"

    result = parse_lines(lines, title="書", author="作者", paragraph_mode="line")
    output = tmp_path / "book.epub"
    render(result.book, output)

    with zipfile.ZipFile(output) as zf:
        xhtml = zf.read("EPUB/text/ch000001.xhtml").decode("utf-8")

    assert xhtml.count("<p") == 3
    assert "第一個段落。" in xhtml
    assert "第二個段落。" in xhtml
    assert "第三個段落。" in xhtml


def test_line_mode_is_explicitly_rejected_for_unknown_values():
    with pytest.raises(ValueError, match="unsupported paragraph mode"):
        parse_lines(["第1章 開始", "正文"], title="書", author="作者", paragraph_mode="auto")

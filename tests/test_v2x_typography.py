from __future__ import annotations

import json
import shutil
import warnings
import zipfile
from pathlib import Path

import pytest

from novel_epub.intermediate import paragraph_from_dict, write_intermediate
from novel_epub.models import Book, Chapter, Paragraph, ParagraphBoundary
from novel_epub.parser import parse_lines
from novel_epub.renderers.pandoc import render


def test_parser_maps_blank_runs_to_following_paragraph():
    result = parse_lines(
        [
            "第1章 開始",
            "第一段",
            "",
            "第二段",
            "",
            "",
            "第三段",
            "",
            "",
            "",
            "第四段",
        ],
        title="書",
        author="作者",
    )
    paragraphs = result.book.chapters[0].paragraphs
    assert [p.text for p in paragraphs] == ["第一段", "第二段", "第三段", "第四段"]
    assert [p.boundary for p in paragraphs] == [
        ParagraphBoundary.NORMAL,
        ParagraphBoundary.NORMAL,
        ParagraphBoundary.EXPANDED,
        ParagraphBoundary.SCENE_BREAK,
    ]


@pytest.mark.parametrize(
    ("blank_lines", "expected"),
    [
        (0, ParagraphBoundary.NORMAL),
        (1, ParagraphBoundary.NORMAL),
        (2, ParagraphBoundary.EXPANDED),
        (3, ParagraphBoundary.SCENE_BREAK),
        (5, ParagraphBoundary.SCENE_BREAK),
    ],
)
def test_parser_maps_blank_run_cardinality_to_following_paragraph(blank_lines, expected):
    result = parse_lines(
        ["第1章 開始", "前一段", *([""] * blank_lines), "後一段"],
        title="書",
        author="作者",
    )
    paragraphs = result.book.chapters[0].paragraphs
    assert [p.boundary for p in paragraphs] == [ParagraphBoundary.NORMAL, expected]


def test_parser_does_not_apply_chapter_start_blank_run_to_previous_paragraph():
    result = parse_lines(
        ["第1章 一", "正文", "", "", "第2章 二", "正文"],
        title="書",
        author="作者",
    )
    chapters = result.book.chapters
    assert chapters[0].paragraphs[0].boundary is ParagraphBoundary.NORMAL
    assert chapters[1].paragraphs[0].boundary is ParagraphBoundary.NORMAL


def test_parser_does_not_apply_chapter_end_blank_run_without_following_paragraph():
    result = parse_lines(
        ["第1章 一", "正文", "", "", ""],
        title="書",
        author="作者",
    )
    paragraphs = result.book.chapters[0].paragraphs
    assert len(paragraphs) == 1
    assert paragraphs[0].boundary is ParagraphBoundary.NORMAL


def test_parser_does_not_cross_volume_boundary_with_pending_blank_run():
    result = parse_lines(
        ["第1卷 上", "第1章 一", "正文", "", "", "第2卷 下", "第2章 二", "正文"],
        title="書",
        author="作者",
    )
    first_volume = result.book.volumes[0]
    second_volume = result.book.volumes[1]
    assert first_volume.chapters[0].paragraphs[0].boundary is ParagraphBoundary.NORMAL
    assert second_volume.chapters[0].paragraphs[0].boundary is ParagraphBoundary.NORMAL


def test_parser_does_not_cross_preamble_to_first_chapter_boundary():
    result = parse_lines(
        ["簡介", "", "", "第1章 開始", "正文"],
        title="書",
        author="作者",
    )
    assert len(result.book.preamble) == 1
    assert result.book.preamble[0].boundary is ParagraphBoundary.NORMAL
    assert result.book.chapters[0].paragraphs[0].boundary is ParagraphBoundary.NORMAL


def test_parser_drops_multiple_blank_runs_before_chapter_heading():
    result = parse_lines(
        ["第1章 一", "正文", "", "", "", "第2章 二", "正文", "", "", "", "第3章 三", "正文"],
        title="書",
        author="作者",
    )
    chapters = result.book.chapters
    assert [chapter.paragraphs[0].boundary for chapter in chapters] == [
        ParagraphBoundary.NORMAL,
        ParagraphBoundary.NORMAL,
        ParagraphBoundary.NORMAL,
    ]


def test_parser_preserves_hard_line_break_and_applies_following_paragraph_boundary():
    result = parse_lines(
        [
            "第1章 開始",
            "第一行",
            "第二行",
            "",
            "",
            "下一段",
        ],
        title="書",
        author="作者",
    )
    paragraphs = result.book.chapters[0].paragraphs
    assert len(paragraphs) == 2
    assert paragraphs[0].text == "第一行\n第二行"
    assert paragraphs[0].boundary is ParagraphBoundary.NORMAL
    assert paragraphs[1].text == "下一段"
    assert paragraphs[1].boundary is ParagraphBoundary.EXPANDED


def test_parser_preserves_hard_line_break_inside_one_paragraph():
    result = parse_lines(
        ["第1章 開始", "第一行", "第二行", "", "下一段"],
        title="書",
        author="作者",
    )
    paragraphs = result.book.chapters[0].paragraphs
    assert len(paragraphs) == 2
    assert paragraphs[0].text == "第一行\n第二行"
    assert paragraphs[0].boundary is ParagraphBoundary.NORMAL


def test_preamble_uses_boundary_semantics_within_its_region():
    result = parse_lines(
        ["簡介", "", "", "補充說明", "第1章 開始", "正文"],
        title="書",
        author="作者",
    )
    assert [p.boundary for p in result.book.preamble] == [
        ParagraphBoundary.NORMAL,
        ParagraphBoundary.EXPANDED,
    ]
    assert result.book.chapters[0].paragraphs[0].boundary is ParagraphBoundary.NORMAL


def test_intermediate_omits_normal_boundary_and_serializes_non_normal(tmp_path: Path):
    book = Book(
        title="書",
        author="作者",
        chapters=[
            Chapter(
                sequence=1,
                number=1,
                label="第1章",
                title="開始",
                paragraphs=[
                    Paragraph("普通"),
                    Paragraph("擴張", ParagraphBoundary.EXPANDED),
                    Paragraph("場景", ParagraphBoundary.SCENE_BREAK),
                ],
            )
        ],
    )
    root = write_intermediate(book, tmp_path / "intermediate")
    chapter = json.loads((root / "chapters/000001.json").read_text(encoding="utf-8"))
    assert chapter["paragraphs"] == [
        {"text": "普通"},
        {"text": "擴張", "boundary": "expanded"},
        {"text": "場景", "boundary": "scene-break"},
    ]


def test_intermediate_missing_boundary_defaults_to_normal():
    paragraph = paragraph_from_dict({"text": "正文"})
    assert paragraph.boundary is ParagraphBoundary.NORMAL


def test_intermediate_invalid_boundary_warns_and_falls_back_to_normal():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        paragraph = paragraph_from_dict({"text": "正文", "boundary": "invalid"})
    assert paragraph.boundary is ParagraphBoundary.NORMAL
    assert any("invalid paragraph boundary" in str(item.message) for item in caught)


def test_renderer_outputs_semantic_boundary_classes(tmp_path: Path):
    if shutil.which("pandoc") is None:
        pytest.skip("Pandoc is not installed in this test environment")
    book = Book(
        title="書",
        author="作者",
        chapters=[
            Chapter(
                sequence=1,
                number=1,
                label="第1章",
                title="開始",
                paragraphs=[
                    Paragraph("普通"),
                    Paragraph("擴張", ParagraphBoundary.EXPANDED),
                    Paragraph("場景", ParagraphBoundary.SCENE_BREAK),
                    Paragraph("第一行\n第二行"),
                ],
            )
        ],
    )
    output = tmp_path / "book.epub"
    render(book, output)
    with zipfile.ZipFile(output) as epub:
        xhtml = epub.read("EPUB/text/ch000001.xhtml").decode("utf-8")
        assert '<p>普通</p>' in xhtml
        assert '<p class="paragraph-expanded">擴張</p>' in xhtml
        assert '<p class="paragraph-scene-break">場景</p>' in xhtml
        assert "第一行<br" in xhtml
        assert "第二行" in xhtml
        css = epub.read("EPUB/styles/stylesheet.css").decode("utf-8")
        assert "line-height: 1.7" in css
        assert "text-indent: 2em" in css
        assert "text-align: left" in css
        assert "break-before: page" in css
        assert "page-break-before: always" in css

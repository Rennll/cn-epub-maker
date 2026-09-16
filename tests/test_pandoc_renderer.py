from __future__ import annotations

import pytest
import zipfile

from novel_epub.models import Book, Chapter, Paragraph, ParagraphBoundary, Volume
from novel_epub.renderers import pandoc


def test_render_preserves_preamble_epub_order_and_language(monkeypatch, tmp_path):
    def fake_run(args, **kwargs):
        destination = args[args.index("--output") + 1]
        pandoc.Path(destination).write_text("<p>rendered</p>", encoding="utf-8")

    monkeypatch.setattr(pandoc.subprocess, "run", fake_run)

    book = Book(
        title="書",
        author="作者",
        language="zh-TW",
        preamble=[Paragraph("作品簡介")],
        chapters=[
            Chapter(sequence=1, number=1, label="第一章", title="開始", paragraphs=[Paragraph("正文")])
        ],
    )
    output = tmp_path / "book.epub"
    pandoc.render(book, output)

    with zipfile.ZipFile(output) as epub:
        assert epub.read("mimetype") == b"application/epub+zip"
        assert epub.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        for info in epub.infolist():
            if info.filename != "mimetype":
                assert info.compress_type == zipfile.ZIP_DEFLATED
        assert "EPUB/text/preamble.xhtml" in epub.namelist()
        preamble = epub.read("EPUB/text/preamble.xhtml").decode("utf-8")
        assert 'lang="zh-TW"' in preamble
        opf = epub.read("EPUB/content.opf").decode("utf-8")
        assert opf.index('idref="preamble"') < opf.index('idref="ch000001"')
        assert '<dc:language>zh-TW</dc:language>' in opf
        assert 'xml:lang="zh-TW"' in opf
        nav = epub.read("EPUB/nav.xhtml").decode("utf-8")
        assert 'lang="zh-TW"' in nav
        assert "前言" in nav


def test_render_keeps_volume_as_navigation_grouping(monkeypatch, tmp_path):
    def fake_run(args, **kwargs):
        destination = args[args.index("--output") + 1]
        pandoc.Path(destination).write_text("<p>rendered</p>", encoding="utf-8")

    monkeypatch.setattr(pandoc.subprocess, "run", fake_run)

    book = Book(
        title="書",
        author="作者",
        volumes=[
            Volume(
                sequence=1,
                number="一",
                label="第一卷",
                title="開始",
                chapters=[
                    Chapter(sequence=1, number=1, label="第一章", title="A", paragraphs=[Paragraph("A")]),
                    Chapter(sequence=2, number=2, label="第二章", title="B", paragraphs=[Paragraph("B")]),
                ],
            )
        ],
    )
    output = tmp_path / "book.epub"
    pandoc.render(book, output)

    with zipfile.ZipFile(output) as epub:
        nav = epub.read("EPUB/nav.xhtml").decode("utf-8")
        opf = epub.read("EPUB/content.opf").decode("utf-8")
        assert "第一卷 開始" in nav
        assert nav.index("第一章 A") < nav.index("第二章 B")
        assert '<item id="ch000001"' in opf
        assert '<item id="ch000002"' in opf
        assert opf.index('idref="ch000001"') < opf.index('idref="ch000002"')
        assert '<item id="volume' not in opf


def test_render_rejects_duplicate_chapter_sequence(monkeypatch, tmp_path):
    def fake_run(args, **kwargs):
        destination = args[args.index("--output") + 1]
        pandoc.Path(destination).write_text("<p>rendered</p>", encoding="utf-8")

    monkeypatch.setattr(pandoc.subprocess, "run", fake_run)

    book = Book(
        title="書",
        author="作者",
        chapters=[
            Chapter(sequence=1, number=1, label="第一章", title="A"),
            Chapter(sequence=1, number=2, label="第二章", title="B"),
        ],
    )

    with pytest.raises(ValueError, match="duplicate chapter sequence"):
        pandoc.render(book, tmp_path / "book.epub")


def test_render_preserves_paragraph_boundaries(monkeypatch, tmp_path):
    def fake_run(args, **kwargs):
        destination = args[args.index("--output") + 1]
        pandoc.Path(destination).write_text(
            "<h1>第一章 A</h1><p>one</p><p>two</p><p>three</p>",
            encoding="utf-8",
        )

    monkeypatch.setattr(pandoc.subprocess, "run", fake_run)

    book = Book(
        title="書",
        author="作者",
        chapters=[
            Chapter(
                sequence=1,
                number=1,
                label="第一章",
                title="A",
                paragraphs=[
                    Paragraph("one"),
                    Paragraph("two", ParagraphBoundary.EXPANDED),
                    Paragraph("three", ParagraphBoundary.SCENE_BREAK),
                ],
            )
        ],
    )

    output = tmp_path / "book.epub"
    pandoc.render(book, output)

    with zipfile.ZipFile(output) as epub:
        chapter = epub.read("EPUB/text/ch000001.xhtml").decode("utf-8")
        assert '<p>one</p>' in chapter
        assert '<p class="paragraph-expanded">two</p>' in chapter
        assert '<p class="paragraph-scene-break">three</p>' in chapter

import shutil
import zipfile
from contextlib import contextmanager
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from novel_epub.models import Book, Chapter, Paragraph, ParagraphBoundary, Volume
from novel_epub.renderers.pandoc import render


XHTML_NS = "http://www.w3.org/1999/xhtml"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"


def _require_pandoc():
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc is required for EPUB semantic renderer tests")


def _book_with_preamble() -> Book:
    return Book(
        title="語義測試書",
        author="測試作者",
        language="zh-TW",
        preamble=[Paragraph(text="這是前言。")],
        volumes=[
            Volume(
                sequence=1,
                number="1",
                label="第一卷",
                title="第一卷",
                chapters=[
                    Chapter(
                        sequence=10,
                        number=1,
                        label="第一章",
                        title="開始",
                        paragraphs=[Paragraph(text="第一章內容。")],
                    ),
                    Chapter(
                        sequence=20,
                        number=2,
                        label="第二章",
                        title="繼續",
                        paragraphs=[Paragraph(text="第二章內容。")],
                    ),
                ],
            )
        ],
        chapters=[
            Chapter(
                sequence=30,
                number=3,
                label="第三章",
                title="卷外章節",
                paragraphs=[Paragraph(text="第三章內容。")],
            )
        ],
    )


@contextmanager
def _read_epub(output: Path):
    with zipfile.ZipFile(output) as zf:
        opf = ET.fromstring(zf.read("EPUB/content.opf"))
        nav = ET.fromstring(zf.read("EPUB/nav.xhtml"))
        yield zf, opf, nav


def test_epub_preamble_is_a_first_class_spine_and_nav_item(tmp_path):
    _require_pandoc()
    output = tmp_path / "book.epub"

    render(_book_with_preamble(), output)

    with _read_epub(output) as (zf, opf, nav):
        names = set(zf.namelist())
        assert "EPUB/text/preamble.xhtml" in names

        manifest = opf.find(f"{{{OPF_NS}}}manifest")
        spine = opf.find(f"{{{OPF_NS}}}spine")
        preamble_item = manifest.find("opf:item[@id='preamble']", {"opf": OPF_NS})
        assert preamble_item is not None
        assert preamble_item.get("href") == "text/preamble.xhtml"

        spine_ids = [item.get("idref") for item in spine.findall(f"{{{OPF_NS}}}itemref")]
        assert spine_ids[0] == "preamble"

        nav_text = " ".join("".join(element.itertext()) for element in nav.iter())
        assert "前言" in nav_text
        assert "text/preamble.xhtml" in " ".join(
            element.get("href", "") for element in nav.iter()
        )

        preamble = ET.fromstring(zf.read("EPUB/text/preamble.xhtml"))
        assert preamble.get("{http://www.w3.org/XML/1998/namespace}lang") == "zh-TW"


def test_epub_without_preamble_has_no_preamble_artifacts(tmp_path):
    _require_pandoc()
    output = tmp_path / "book.epub"
    book = _book_with_preamble()
    book.preamble = []

    render(book, output)

    with _read_epub(output) as (zf, opf, nav):
        assert "EPUB/text/preamble.xhtml" not in zf.namelist()
        manifest = opf.find(f"{{{OPF_NS}}}manifest")
        assert manifest.find("opf:item[@id='preamble']", {"opf": OPF_NS}) is None
        assert not any(
            item.get("idref") == "preamble"
            for item in opf.find(f"{{{OPF_NS}}}spine").findall(f"{{{OPF_NS}}}itemref")
        )
        assert "前言" not in " ".join("".join(element.itertext()) for element in nav.iter())


def test_epub_order_and_metadata_follow_book_semantics(tmp_path):
    _require_pandoc()
    output = tmp_path / "book.epub"

    render(_book_with_preamble(), output)

    with _read_epub(output) as (zf, opf, nav):
        metadata = opf.find(f"{{{OPF_NS}}}metadata")
        assert metadata.find(f"{{{DC_NS}}}title").text == "語義測試書"
        assert metadata.find(f"{{{DC_NS}}}creator").text == "測試作者"
        assert metadata.find(f"{{{DC_NS}}}language").text == "zh-TW"
        assert opf.get("{http://www.w3.org/XML/1998/namespace}lang") == "zh-TW"

        manifest = opf.find(f"{{{OPF_NS}}}manifest")
        spine = opf.find(f"{{{OPF_NS}}}spine")
        chapter_items = {
            item.get("id"): item.get("href")
            for item in manifest.findall(f"{{{OPF_NS}}}item")
            if item.get("media-type") == "application/xhtml+xml" and item.get("id") != "preamble"
        }
        spine_chapters = [
            item.get("idref")
            for item in spine.findall(f"{{{OPF_NS}}}itemref")
            if item.get("idref") != "preamble"
        ]
        assert spine_chapters == ["ch000001", "ch000002", "ch000003"]
        assert chapter_items == {
            "ch000001": "text/ch000010.xhtml",
            "ch000002": "text/ch000020.xhtml",
            "ch000003": "text/ch000030.xhtml",
        }
        assert all(href.removeprefix("../") in zf.namelist() for href in chapter_items.values())

        nav_links = [
            element.get("href")
            for element in nav.iter(f"{{{XHTML_NS}}}a")
            if element.get("href")
        ]
        assert nav_links == [
            "text/ch000010.xhtml",
            "text/ch000020.xhtml",
            "text/ch000030.xhtml",
        ]

        volume_lists = [
            element
            for element in nav.iter(f"{{{XHTML_NS}}}li")
            if "第一卷" in "".join(element.itertext())
        ]
        assert volume_lists

        container = ET.fromstring(zf.read("META-INF/container.xml"))
        rootfile = container.find(f"{{{CONTAINER_NS}}}rootfiles/{{{CONTAINER_NS}}}rootfile")
        assert rootfile.get("full-path") == "EPUB/content.opf"
        assert "EPUB/nav.xhtml" in zf.namelist()
        assert "EPUB/styles/stylesheet.css" in zf.namelist()

        with zf.open("mimetype") as mimetype:
            assert mimetype.read() == b"application/epub+zip"
        assert zf.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert zf.namelist()[0] == "mimetype"


def test_epub_cover_is_manifested_only_when_present(tmp_path):
    _require_pandoc()
    output = tmp_path / "book.epub"
    book = _book_with_preamble()
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"not-a-real-png-but-a-valid-test-fixture")
    book.cover = str(cover)

    render(book, output)

    with _read_epub(output) as (zf, opf, _nav):
        manifest = opf.find(f"{{{OPF_NS}}}manifest")
        cover_item = manifest.find("opf:item[@id='cover-image']", {"opf": OPF_NS})
        assert cover_item is not None
        assert cover_item.get("media-type") == "image/png"
        assert "EPUB/images/cover.png" in zf.namelist()
        cover_meta = opf.find(
            ".//opf:meta[@name='cover']",
            {"opf": OPF_NS},
        )
        assert cover_meta is not None
        assert cover_meta.get("content") == "cover-image"

    output_without_cover = tmp_path / "book-without-cover.epub"
    book.cover = None
    render(book, output_without_cover)

    with _read_epub(output_without_cover) as (zf, opf, _nav):
        manifest = opf.find(f"{{{OPF_NS}}}manifest")
        assert manifest.find("opf:item[@id='cover-image']", {"opf": OPF_NS}) is None
        assert not any(name.startswith("EPUB/images/") for name in zf.namelist())
        assert opf.find(".//opf:meta[@name='cover']", {"opf": OPF_NS}) is None


def test_epub_paragraph_boundaries_map_to_xhtml_paragraphs(tmp_path):
    _require_pandoc()
    output = tmp_path / "book.epub"
    book = Book(
        title="段落語義測試",
        author="測試作者",
        language="zh-TW",
        chapters=[
            Chapter(
                sequence=1,
                number=1,
                label="第一章",
                title="段落",
                paragraphs=[
                    Paragraph(text="一般段落"),
                    Paragraph(text="展開段落", boundary=ParagraphBoundary.EXPANDED),
                    Paragraph(text="場景切換", boundary=ParagraphBoundary.SCENE_BREAK),
                ],
            )
        ],
    )

    render(book, output)

    with zipfile.ZipFile(output) as zf:
        chapter = ET.fromstring(zf.read("EPUB/text/ch000001.xhtml"))
        classes = [p.get("class") for p in chapter.iter(f"{{{XHTML_NS}}}p")]
        assert classes == [None, "paragraph-expanded", "paragraph-scene-break"]

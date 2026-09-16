import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from novel_epub.models import Book, Chapter, Paragraph, ParagraphBoundary, Volume
from novel_epub.renderers.pandoc import render

XHTML_NS = "http://www.w3.org/1999/xhtml"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
EPUB_NS = "http://www.idpf.org/2007/ops"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"


def _require_pandoc():
    if shutil.which("pandoc") is None:
        pytest.skip("Pandoc is not installed in this test environment")


def _book_with_preamble() -> Book:
    return Book(
        title="語義測試書",
        author="測試作者",
        language="zh-TW",
        preamble=[Paragraph("這是前言。")],
        volumes=[
            Volume(
                sequence=1,
                number="1",
                label="第一卷",
                title="起始",
                chapters=[
                    Chapter(
                        sequence=10,
                        number="1",
                        label="第1章",
                        title="卷內第一章",
                        paragraphs=[Paragraph("卷內內容。"), Paragraph("第二段。")],
                    ),
                    Chapter(
                        sequence=20,
                        number="2",
                        label="第2章",
                        title="卷內第二章",
                        paragraphs=[Paragraph("第二章內容。")],
                    ),
                ],
            )
        ],
        chapters=[
            Chapter(
                sequence=30,
                number="3",
                label="第3章",
                title="卷外章節",
                paragraphs=[Paragraph("卷外內容。")],
            )
        ],
    )


def _read_epub(output: Path):
    zf = zipfile.ZipFile(output)
    opf = ET.fromstring(zf.read("EPUB/content.opf"))
    nav = ET.fromstring(zf.read("EPUB/nav.xhtml"))
    return zf, opf, nav


def test_epub_preamble_is_a_first_class_spine_and_nav_item(tmp_path: Path):
    _require_pandoc()
    output = tmp_path / "with-preamble.epub"
    render(_book_with_preamble(), output)

    with _read_epub(output) as (zf, opf, nav):
        manifest = {item.attrib["id"]: item for item in opf.findall(f"{{{OPF_NS}}}manifest/{{{OPF_NS}}}item")}
        spine = [item.attrib["idref"] for item in opf.findall(f"{{{OPF_NS}}}spine/{{{OPF_NS}}}itemref")]
        nav_links = nav.findall(f".//{{{XHTML_NS}}}a")

        assert "EPUB/text/preamble.xhtml" in zf.namelist()
        assert manifest["preamble"].attrib["href"] == "text/preamble.xhtml"
        assert spine[0] == "preamble"
        assert nav_links[0].attrib["href"] == "text/preamble.xhtml"
        assert nav_links[0].text == "前言"

        preamble = ET.fromstring(zf.read("EPUB/text/preamble.xhtml"))
        assert preamble.attrib["lang"] == "zh-TW"
        assert preamble.attrib["{http://www.w3.org/XML/1998/namespace}lang"] == "zh-TW"


def test_epub_without_preamble_has_no_preamble_artifacts(tmp_path: Path):
    _require_pandoc()
    book = Book(
        title="無前言",
        author="作者",
        chapters=[Chapter(sequence=1, number="1", label="第1章", title="章節", paragraphs=[Paragraph("內容。")])],
    )
    output = tmp_path / "without-preamble.epub"
    render(book, output)

    with _read_epub(output) as (zf, opf, nav):
        names = set(zf.namelist())
        manifest_hrefs = {item.attrib["href"] for item in opf.findall(f"{{{OPF_NS}}}manifest/{{{OPF_NS}}}item")}
        spine = [item.attrib["idref"] for item in opf.findall(f"{{{OPF_NS}}}spine/{{{OPF_NS}}}itemref")]
        nav_hrefs = [link.attrib["href"] for link in nav.findall(f".//{{{XHTML_NS}}}a")]

        assert "EPUB/text/preamble.xhtml" not in names
        assert "text/preamble.xhtml" not in manifest_hrefs
        assert "preamble" not in spine
        assert "text/preamble.xhtml" not in nav_hrefs


def test_epub_order_and_metadata_follow_book_semantics(tmp_path: Path):
    _require_pandoc()
    output = tmp_path / "semantics.epub"
    render(_book_with_preamble(), output)

    with _read_epub(output) as (zf, opf, nav):
        ns = {"opf": OPF_NS, "dc": DC_NS}
        metadata = opf.find("opf:metadata", ns)
        assert metadata is not None
        assert metadata.find("dc:title", ns).text == "語義測試書"
        assert metadata.find("dc:creator", ns).text == "測試作者"
        assert metadata.find("dc:language", ns).text == "zh-TW"
        assert opf.attrib["{http://www.w3.org/XML/1998/namespace}lang"] == "zh-TW"
        assert nav.attrib["lang"] == "zh-TW"
        assert nav.attrib["{http://www.w3.org/XML/1998/namespace}lang"] == "zh-TW"

        manifest = {item.attrib["id"]: item for item in opf.findall("opf:manifest/opf:item", ns)}
        spine = [itemref.attrib["idref"] for itemref in opf.findall("opf:spine/opf:itemref", ns)]
        spine_hrefs = [manifest[item_id].attrib["href"] for item_id in spine]
        assert spine_hrefs == [
            "text/preamble.xhtml",
            "text/ch000010.xhtml",
            "text/ch000020.xhtml",
            "text/ch000030.xhtml",
        ]

        nav_links = nav.findall(f".//{{{XHTML_NS}}}a")
        assert [link.attrib["href"] for link in nav_links] == [
            "text/preamble.xhtml",
            "text/ch000010.xhtml",
            "text/ch000020.xhtml",
            "text/ch000030.xhtml",
        ]
        assert [link.text for link in nav_links[1:]] == [
            "第1章 卷內第一章",
            "第2章 卷內第二章",
            "第3章 卷外章節",
        ]

        for item in manifest.values():
            href = item.attrib["href"]
            if href.startswith("text/") or href == "styles/stylesheet.css":
                assert f"EPUB/{href}" in zf.namelist()

        rootfile = ET.fromstring(zf.read("META-INF/container.xml")).find(
            f"{{{CONTAINER_NS}}}rootfiles/{{{CONTAINER_NS}}}rootfile"
        )
        assert rootfile is not None
        assert rootfile.attrib["full-path"] == "EPUB/content.opf"


def test_epub_cover_is_manifested_only_when_present(tmp_path: Path):
    _require_pandoc()
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"not-a-real-png-but-a-valid-test-fixture")
    book = Book(
        title="封面測試",
        author="作者",
        cover=str(cover),
        chapters=[Chapter(sequence=1, number="1", label="第1章", title="章節")],
    )
    output = tmp_path / "cover.epub"
    render(book, output)

    with _read_epub(output) as (zf, opf, _nav):
        manifest = {item.attrib["id"]: item for item in opf.findall(f"{{{OPF_NS}}}manifest/{{{OPF_NS}}}item")}
        assert "cover-image" in manifest
        assert manifest["cover-image"].attrib["href"] == "images/cover.png"
        assert manifest["cover-image"].attrib["properties"] == "cover-image"
        assert "EPUB/images/cover.png" in zf.namelist()


def test_epub_paragraph_boundaries_map_to_xhtml_paragraphs(tmp_path: Path):
    _require_pandoc()
    book = Book(
        title="段落測試",
        author="作者",
        chapters=[
            Chapter(
                sequence=1,
                number="1",
                label="第1章",
                title="段落",
                paragraphs=[
                    Paragraph("普通段落", ParagraphBoundary.NORMAL),
                    Paragraph("展開段落", ParagraphBoundary.EXPANDED),
                    Paragraph("場景切換", ParagraphBoundary.SCENE_BREAK),
                ],
            )
        ],
    )
    output = tmp_path / "paragraphs.epub"
    render(book, output)

    with zipfile.ZipFile(output) as zf:
        chapter = ET.fromstring(zf.read("EPUB/text/ch000001.xhtml"))
        paragraphs = chapter.findall(f".//{{{XHTML_NS}}}p")
        assert [paragraph.text for paragraph in paragraphs] == ["普通段落", "展開段落", "場景切換"]
        assert [paragraph.attrib.get("class") for paragraph in paragraphs] == [
            None,
            "paragraph-expanded",
            "paragraph-scene-break",
        ]

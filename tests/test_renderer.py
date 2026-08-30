import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from novel_epub.models import Book, Chapter, Paragraph, Volume
from novel_epub.renderers.pandoc import _markdown, render


def make_book() -> Book:
    book = Book(title="測試書", author="作者")
    book.volumes.append(Volume(sequence=1, number="1", label="第一卷", title="九洲一号群", chapters=[
        Chapter(sequence=1, number="1", label="第1章", title="黄山真君和九洲一号群",
                paragraphs=[Paragraph("2019年5月20日，星期一。"), Paragraph("a < b & c > d")])
    ]))
    book.volumes.append(Volume(sequence=2, number="2", label="第二卷", title="武道筑基", chapters=[
        Chapter(sequence=2, number="26", label="第26章", title="我那与众不同的炼丹炉",
                paragraphs=[Paragraph("平静的上完了最后一节课……")])
    ]))
    return book


def test_markdown_preserves_volume_and_chapter_hierarchy():
    md = _markdown(make_book())
    assert "# 第一卷 九洲一号群" in md
    assert "## 第1章 黄山真君和九洲一号群" in md
    assert "# 第二卷 武道筑基" in md
    assert "## 第26章 我那与众不同的炼丹炉" in md
    assert "a < b & c \\> d" in md


def test_render_requires_pandoc(tmp_path: Path):
    if shutil.which("pandoc") is None:
        pytest.skip("Pandoc is not installed in this test environment")
    output = tmp_path / "book.epub"
    render(make_book(), output)
    assert output.is_file()

    with zipfile.ZipFile(output) as zf:
        names = set(zf.namelist())
        assert "mimetype" in names
        assert "META-INF/container.xml" in names
        assert "EPUB/content.opf" in names
        assert "EPUB/nav.xhtml" in names
        assert "EPUB/styles/stylesheet.css" in names
        assert "EPUB/text/ch000001.xhtml" in names
        assert "EPUB/text/ch000002.xhtml" in names

        nav_text = zf.read("EPUB/nav.xhtml").decode("utf-8")
        assert "第一卷 九洲一号群" in nav_text
        assert "第二卷 武道筑基" in nav_text
        assert "第1章 黄山真君和九洲一号群" in nav_text
        assert "第26章 我那与众不同的炼丹炉" in nav_text
        assert nav_text.index("第一卷") < nav_text.index("第1章") < nav_text.index("第二卷") < nav_text.index("第26章")

        opf_root = ET.fromstring(zf.read("EPUB/content.opf"))
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        manifest = {item.attrib["id"]: item for item in opf_root.findall("opf:manifest/opf:item", ns)}
        spine_ids = [itemref.attrib["idref"] for itemref in opf_root.findall("opf:spine/opf:itemref", ns)]
        spine_hrefs = [manifest[item_id].attrib["href"] for item_id in spine_ids]
        assert spine_hrefs == ["text/ch000001.xhtml", "text/ch000002.xhtml"]

        first = zf.read("EPUB/text/ch000001.xhtml").decode("utf-8")
        assert "a &lt; b &amp; c &gt; d" in first


def test_epub_renderer_contract_links_manifest_spine_and_content(tmp_path: Path):
    if shutil.which("pandoc") is None:
        pytest.skip("Pandoc is not installed in this test environment")

    output = tmp_path / "book.epub"
    render(make_book(), output)

    with zipfile.ZipFile(output) as zf:
        infos = zf.infolist()
        assert infos[0].filename == "mimetype"
        assert infos[0].compress_type == zipfile.ZIP_STORED
        assert zf.read("mimetype") == b"application/epub+zip"

        container = ET.fromstring(zf.read("META-INF/container.xml"))
        container_ns = "urn:oasis:names:tc:opendocument:xmlns:container"
        rootfile = container.find(f"{{{container_ns}}}rootfiles/{{{container_ns}}}rootfile")
        assert rootfile is not None
        assert rootfile.attrib["full-path"] == "EPUB/content.opf"
        assert rootfile.attrib["media-type"] == "application/oebps-package+xml"

        opf = ET.fromstring(zf.read("EPUB/content.opf"))
        opf_ns = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
        assert opf.attrib["version"] == "3.0"
        metadata = opf.find("opf:metadata", opf_ns)
        assert metadata is not None
        assert metadata.find("dc:title", opf_ns).text == "測試書"
        assert metadata.find("dc:creator", opf_ns).text == "作者"
        assert metadata.find("dc:language", opf_ns).text == "zh-CN"

        manifest = {item.attrib["id"]: item for item in opf.findall("opf:manifest/opf:item", opf_ns)}
        spine = [itemref.attrib["idref"] for itemref in opf.findall("opf:spine/opf:itemref", opf_ns)]
        assert spine == ["ch000001", "ch000002"]

        for item in manifest.values():
            assert f"EPUB/{item.attrib['href']}" in zf.namelist()
        for item_id in spine:
            item = manifest[item_id]
            assert item.attrib["media-type"] == "application/xhtml+xml"
            assert item.attrib["href"].startswith("text/")

        nav = ET.fromstring(zf.read("EPUB/nav.xhtml"))
        nav_epub_ns = "http://www.idpf.org/2007/ops"
        toc = nav.find(f".//*[@{{{nav_epub_ns}}}type='toc']")
        assert toc is not None
        links = nav.findall(".//{http://www.w3.org/1999/xhtml}a")
        assert [link.attrib["href"] for link in links] == ["text/ch000001.xhtml", "text/ch000002.xhtml"]

        xhtml_ns = {"x": "http://www.w3.org/1999/xhtml"}
        for href in ["text/ch000001.xhtml", "text/ch000002.xhtml"]:
            chapter = ET.fromstring(zf.read(f"EPUB/{href}"))
            title = chapter.find("./x:head/x:title", xhtml_ns)
            stylesheet = chapter.find("./x:head/x:link[@rel='stylesheet']", xhtml_ns)
            assert title is not None
            assert stylesheet is not None
            assert stylesheet.attrib["href"] == "../styles/stylesheet.css"


def test_epub_renderer_contract_rejects_duplicate_chapter_sequences(tmp_path: Path):
    if shutil.which("pandoc") is None:
        pytest.skip("Pandoc is not installed in this test environment")
    book = Book(title="測試書", author="作者", chapters=[
        Chapter(sequence=1, number="1", label="第1章", title="甲"),
        Chapter(sequence=1, number="2", label="第2章", title="乙"),
    ])
    with pytest.raises(ValueError, match="duplicate chapter sequence"):
        render(book, tmp_path / "book.epub")

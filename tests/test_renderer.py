import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import unquote
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

        nav_name = next(n for n in names if n.endswith("nav.xhtml"))
        nav_text = zf.read(nav_name).decode("utf-8")
        assert "第一卷" in nav_text and "第二卷" in nav_text
        assert "第1章" in nav_text and "第26章" in nav_text

        opf_name = next(n for n in names if n.endswith(".opf"))
        opf_root = ET.fromstring(zf.read(opf_name))
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        manifest = {item.attrib["id"]: item for item in opf_root.findall("opf:manifest/opf:item", ns)}
        spine_ids = [itemref.attrib["idref"] for itemref in opf_root.findall("opf:spine/opf:itemref", ns)]
        spine_hrefs = [manifest[item_id].attrib["href"] for item_id in spine_ids]
        chapter_hrefs = [href for href in spine_hrefs if href.startswith("text/ch")]

        opf_dir = Path(opf_name).parent.as_posix()
        print("EPUB diagnostic content documents:")
        for href in chapter_hrefs:
            zip_path = unquote(f"{opf_dir}/{href}" if opf_dir != "." else href)
            text = zf.read(zip_path).decode("utf-8")
            title = re.search(r"<title>(.*?)</title>", text, re.S)
            headings = re.findall(r"<h([1-6])[^>]*>(.*?)</h\1>", text, re.S)
            print(f"  {zip_path}: title={title.group(1) if title else '<none>'!r}")
            for level, heading in headings:
                print(f"    h{level}: {heading!r}")

        print("EPUB diagnostic nav entries:")
        print(nav_text)

        # Pandoc must create one content document per chapter. A volume is a
        # navigation parent, not an EPUB content document of its own.
        assert len(chapter_hrefs) == 2

import shutil
import zipfile
from pathlib import Path

import pytest

from novel_epub.models import Book, Chapter, Paragraph, Volume
from novel_epub.renderers.pandoc import _markdown, render


def make_book() -> Book:
    book = Book(title="測試書", author="作者")
    book.volumes.append(
        Volume(
            sequence=1, number="1", label="第一卷", title="九洲一号群",
            chapters=[Chapter(sequence=1, number="1", label="第1章", title="黄山真君和九洲一号群",
                              paragraphs=[Paragraph("2019年5月20日，星期一。"), Paragraph("a < b & c > d")])],
        )
    )
    book.volumes.append(
        Volume(
            sequence=2, number="2", label="第二卷", title="武道筑基",
            chapters=[Chapter(sequence=2, number="26", label="第26章", title="我那与众不同的炼丹炉",
                              paragraphs=[Paragraph("平静的上完了最后一节课……")])],
        )
    )
    return book


def test_markdown_preserves_volume_and_chapter_hierarchy():
    md = _markdown(make_book())
    assert "# 第一卷 九洲一号群" in md
    assert "## 第1章 黄山真君和九洲一号群" in md
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
        nav = next((n for n in names if n.endswith("nav.xhtml")), None)
        assert nav is not None
        nav_text = zf.read(nav).decode("utf-8")
        assert "第一卷" in nav_text
        assert "第二卷" in nav_text
        assert "第1章" in nav_text
        assert "第26章" in nav_text

        content_files = [n for n in names if n.endswith(".xhtml") and "nav" not in n]
        assert len(content_files) >= 2
        content_text = "\n".join(zf.read(n).decode("utf-8") for n in content_files)
        assert "a &lt; b &amp; c &gt; d" in content_text

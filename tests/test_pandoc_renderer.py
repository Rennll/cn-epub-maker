from __future__ import annotations

import zipfile

from novel_epub.models import Book, Chapter, Paragraph
from novel_epub.renderers import pandoc


def test_render_preserves_preamble_and_epub_order(monkeypatch, tmp_path):
    def fake_pandoc(source, destination):
        destination.write_text("<p>rendered</p>", encoding="utf-8")

    monkeypatch.setattr(pandoc, "subprocess", type("Subprocess", (), {"run": staticmethod(lambda args, **kwargs: fake_pandoc(type("Source", (), {"read_text": lambda self, encoding=None: ""})(), Path(args[-1])))})())

    book = Book(
        title="書",
        author="作者",
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
        opf = epub.read("EPUB/content.opf").decode("utf-8")
        assert opf.index('idref="preamble"') < opf.index('idref="ch000001"')
        nav = epub.read("EPUB/nav.xhtml").decode("utf-8")
        assert "前言" in nav

from pathlib import Path
from zipfile import ZipFile

from novel_epub.models import Book, Chapter, Paragraph
from novel_epub.parser_stages import WarningItem
from novel_epub.validation.book import validate_book
from novel_epub.validation.epub import validate_epub
from novel_epub.validation.epubcheck import run_epubcheck


def test_book_validation_is_independent_of_epub_validation():
    book = Book(title="測試書", author="作者", chapters=[
        Chapter(sequence=1, number="1", label="第1章", title="空章"),
    ])
    warnings: list[WarningItem] = []

    report = validate_book(book, warnings)

    assert report.errors == []
    assert len(report.warnings) == 1
    assert report.warnings[0].code == "empty_chapter"


def test_book_validation_reports_semantic_errors_without_an_epub(tmp_path: Path):
    book = Book(title="", author="", chapters=[])
    warnings: list[WarningItem] = []

    report = validate_book(book, warnings)

    assert report.ok is False
    assert report.errors == [
        "book title is empty",
        "author is empty",
        "book contains no chapters",
    ]
    assert not (tmp_path / "book.epub").exists()


def test_epub_validation_is_independent_of_book_model():
    path = Path("/tmp/nonexistent-validation-test.epub")

    assert validate_epub(path) == [f"EPUB not found: {path}"]


def test_epub_validation_can_validate_a_generated_archive(tmp_path: Path):
    path = tmp_path / "book.epub"
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml" /></rootfiles>
</container>
'''
    opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Book</dc:title></metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />
    <item id="ch1" href="text/ch000001.xhtml" media-type="application/xhtml+xml" />
  </manifest>
  <spine><itemref idref="ch1" /></spine>
</package>
'''
    nav = '''<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <body><nav epub:type="toc"><a href="text/ch000001.xhtml">Chapter</a></nav></body>
</html>
'''
    with ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("EPUB/content.opf", opf)
        zf.writestr("EPUB/nav.xhtml", nav)
        zf.writestr("EPUB/text/ch000001.xhtml", "<html />")

    assert validate_epub(path) == []


def test_epubcheck_can_be_exercised_without_running_epubcheck(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("novel_epub.validation.epubcheck.shutil.which", lambda name: None)

    result = run_epubcheck(tmp_path / "book.epub")

    assert result.available is False
    assert result.ok is True
    assert result.errors == []

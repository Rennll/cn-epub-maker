from __future__ import annotations

from dataclasses import dataclass
from zipfile import ZipFile
from pathlib import Path

from .models import Book
from .parser import WarningItem


@dataclass
class ValidationReport:
    errors: list[str]
    warnings: list[WarningItem]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_book(book: Book, warnings: list[WarningItem]) -> ValidationReport:
    errors: list[str] = []
    if not book.title.strip():
        errors.append("book title is empty")
    if not book.author.strip():
        errors.append("author is empty")
    if book.chapter_count == 0:
        errors.append("book contains no chapters")
    for chapter in book.iter_chapters():
        if not chapter.paragraphs:
            warnings.append(WarningItem("empty_chapter", 0, f"empty chapter: {chapter.label}"))
    return ValidationReport(errors, warnings)


def validate_epub(path: str | Path) -> list[str]:
    errors: list[str] = []
    path = Path(path)
    if not path.is_file():
        return [f"EPUB not found: {path}"]
    try:
        with ZipFile(path) as zf:
            names = zf.namelist()
            if not names or names[0] != "mimetype":
                errors.append("mimetype must be the first EPUB archive entry")
            elif zf.read("mimetype") != b"application/epub+zip":
                errors.append("invalid EPUB mimetype")
            for required in ("META-INF/container.xml",):
                if required not in names:
                    errors.append(f"missing required EPUB file: {required}")
    except Exception as exc:
        errors.append(f"invalid EPUB archive: {exc}")
    return errors

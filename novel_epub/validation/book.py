from __future__ import annotations

from ..models import Book
from ..parser_stages import WarningItem
from .report import ValidationReport


def validate_book(book: Book, warnings: list[WarningItem]) -> ValidationReport:
    """Validate semantic invariants of a parsed Book model."""
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
    return ValidationReport(errors=errors, warnings=warnings)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .analysis import DocumentAnalysis, analyze_document
from .dfm import DocumentFormattingModel, build_formatting_model
from .models import Book
from .parser_stages import (
    DEFAULT_CHAPTER_PATTERN,
    DEFAULT_VOLUME_PATTERN,
    BookBuilder,
    HeadingDetector,
    ParagraphMode,
    StructuralEventGenerator,
    WarningItem,
)
from .physical import PhysicalDocument, build_physical_document


@dataclass
class ParseResult:
    book: Book
    warnings: list[WarningItem]
    analysis: DocumentAnalysis | None = None
    formatting_model: DocumentFormattingModel | None = None


def parse_document(
    document: PhysicalDocument,
    *,
    title: str,
    author: str,
    language: str = "zh-TW",
    cover: str | None = None,
    volume_pattern: str = DEFAULT_VOLUME_PATTERN,
    chapter_pattern: str = DEFAULT_CHAPTER_PATTERN,
    paragraph_mode: ParagraphMode = "wrapped",
    analysis: DocumentAnalysis | None = None,
    formatting_model: DocumentFormattingModel | None = None,
) -> ParseResult:
    """Orchestrate analysis, structural event generation, and book construction."""
    if formatting_model is None:
        if analysis is None:
            analysis = analyze_document(document)
        formatting_model = build_formatting_model(document, analysis)
    else:
        if formatting_model.physical_document is not document:
            raise ValueError("formatting_model must use the supplied PhysicalDocument")
        if analysis is not None and formatting_model.analysis is not analysis:
            raise ValueError("formatting_model must use the supplied DocumentAnalysis")
        analysis = formatting_model.analysis

    events = StructuralEventGenerator(
        HeadingDetector(
            volume_pattern=volume_pattern,
            chapter_pattern=chapter_pattern,
        )
    ).generate(document)
    book, warnings = BookBuilder(
        title=title,
        author=author,
        language=language,
        cover=cover,
        paragraph_mode=paragraph_mode,
    ).build(events)
    return ParseResult(
        book=book,
        warnings=warnings,
        analysis=analysis,
        formatting_model=formatting_model,
    )


def parse_lines(
    lines: list[str],
    *,
    title: str,
    author: str,
    language: str = "zh-TW",
    cover: str | None = None,
    volume_pattern: str = DEFAULT_VOLUME_PATTERN,
    chapter_pattern: str = DEFAULT_CHAPTER_PATTERN,
    paragraph_mode: ParagraphMode = "wrapped",
    physical_document: PhysicalDocument | None = None,
    analysis: DocumentAnalysis | None = None,
    formatting_model: DocumentFormattingModel | None = None,
) -> ParseResult:
    """Compatibility wrapper around the shared physical-document parser."""
    document = physical_document or build_physical_document(lines)
    return parse_document(
        document,
        title=title,
        author=author,
        language=language,
        cover=cover,
        volume_pattern=volume_pattern,
        chapter_pattern=chapter_pattern,
        paragraph_mode=paragraph_mode,
        analysis=analysis,
        formatting_model=formatting_model,
    )

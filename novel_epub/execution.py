from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .analysis import analyze_document
from .configuration import ConversionRequest, TransformationPolicy
from .dfm import build_formatting_model
from .intermediate import write_intermediate
from .normalize import read_lines
from .parser import parse_lines
from .physical import build_physical_document
from .renderers.pandoc import RenderingError, render
from .transforms import (
    JunkCleaner,
    OpenCCTransformer,
    PunctuationTransformer,
    TransformAudit,
    TransformPipeline,
    TransformationError,
)
from .validator import ValidationReport, validate_book, validate_epub


@dataclass(frozen=True)
class BookSummary:
    title: str
    author: str
    volumes: int
    chapters: int
    paragraphs: int

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "author": self.author,
            "volumes": self.volumes,
            "chapters": self.chapters,
            "paragraphs": self.paragraphs,
        }


@dataclass
class ExecutionResult:
    return_code: int
    encoding: str = ""
    book_summary: dict[str, object] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    audit: list[TransformAudit] = field(default_factory=list)
    epub_path: Path | None = None
    intermediate_path: Path | None = None
    errors: list[str] = field(default_factory=list)
    validation: ValidationReport | None = None
    epub_validation_errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.return_code == 0


def _run_transformations(
    lines: list[str],
    policy: TransformationPolicy,
    *,
    full_source: bool,
) -> tuple[list[str], list[TransformAudit]]:
    if full_source:
        return lines, []

    transformers = [JunkCleaner(rules=list(policy.junk_cleaner.rules))]
    if policy.opencc.enabled:
        transformers.append(OpenCCTransformer(profile=policy.opencc.profile))
    if policy.punctuation_enabled:
        transformers.append(PunctuationTransformer())

    text, audit = TransformPipeline(transformers).run("\n".join(lines))
    return text.split("\n"), audit


def _book_summary(book) -> dict[str, object]:
    return BookSummary(
        title=book.title,
        author=book.author,
        volumes=len(book.volumes),
        chapters=book.chapter_count,
        paragraphs=book.paragraph_count,
    ).to_dict()


def _warning_messages(audit: list[TransformAudit], warnings) -> list[str]:
    messages = [f"{stage.name}: {warning}" for stage in audit for warning in stage.warnings]
    messages.extend(
        f"{warning.message}{f' at line {warning.line}' if warning.line else ''}"
        for warning in warnings
    )
    return messages


def execute(
    request: ConversionRequest,
    *,
    keep_intermediate: bool = False,
    intermediate: str | None = None,
) -> ExecutionResult:
    """Execute a conversion without producing console output side effects."""
    execution = ExecutionResult(return_code=1)
    try:
        requested_encoding = (
            None if request.policy.encoding == "auto" else request.policy.encoding
        )
        lines, encoding = read_lines(request.source, requested_encoding)
        execution.encoding = encoding
        lines, audit = _run_transformations(
            lines,
            request.policy.transformations,
            full_source=request.policy.full_source,
        )
        execution.audit = audit

        # PhysicalDocument is the single shared post-transformation representation.
        physical_document = build_physical_document(lines)
        analysis = analyze_document(physical_document)
        formatting_model = build_formatting_model(physical_document, analysis)
        result = parse_lines(
            lines,
            title=request.book_metadata.title,
            author=request.book_metadata.author,
            language=request.book_metadata.language,
            cover=request.book_metadata.cover,
            paragraph_mode=request.policy.parser.paragraph_mode,
            physical_document=physical_document,
            analysis=analysis,
            formatting_model=formatting_model,
        )
        execution.book_summary = _book_summary(result.book)
        report = validate_book(result.book, result.warnings)
        execution.validation = report
        validation_warnings = getattr(report, "warnings", [])
        execution.warnings = _warning_messages(audit, validation_warnings)
        if report.errors:
            execution.return_code = 2
            execution.errors = list(report.errors)
            return execution

        if keep_intermediate:
            intermediate_path = Path(
                intermediate or Path(request.source).with_suffix("").name + ".intermediate"
            )
            execution.intermediate_path = write_intermediate(
                result.book, intermediate_path, transformations=audit
            )

        render(result.book, request.destination)
        execution.epub_path = Path(request.destination)
        execution.epub_validation_errors = validate_epub(request.destination)
        if execution.epub_validation_errors:
            execution.return_code = 3
            execution.errors = list(execution.epub_validation_errors)
            return execution

        execution.return_code = 0
        return execution
    except TransformationError as exc:
        execution.errors = [str(exc)]
    except RenderingError as exc:
        execution.errors = [str(exc)]
    except FileNotFoundError as exc:
        execution.errors = [f"required executable or file not found: {exc}"]
    except (OSError, ValueError, UnicodeError) as exc:
        execution.errors = [str(exc)]
    return execution

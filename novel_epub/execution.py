from __future__ import annotations

import sys
from pathlib import Path

from .configuration import ConversionRequest, TransformationPolicy
from .intermediate import write_intermediate
from .normalize import normalize_line, read_lines
from .parser import parse_lines
from .renderers.pandoc import render
from .transforms import (
    JunkCleaner,
    OpenCCTransformer,
    PunctuationTransformer,
    TransformAudit,
    TransformPipeline,
    TransformationError,
)
from .validator import validate_book, validate_epub


def _run_transformations(
    lines: list[str],
    policy: TransformationPolicy,
    *,
    full_source: bool,
) -> tuple[list[str], list[TransformAudit]]:
    if full_source:
        return lines, []

    transformers = [JunkCleaner()]
    if policy.opencc.enabled:
        transformers.append(OpenCCTransformer(profile=policy.opencc.profile))
    if policy.punctuation_enabled:
        transformers.append(PunctuationTransformer())

    text, audit = TransformPipeline(transformers).run("\n".join(lines))
    return text.split("\n"), audit


def _print_transform_audit(audit: list[TransformAudit]) -> None:
    for stage in audit:
        if stage.name == "opencc":
            profile = stage.metadata.get("profile", "unknown")
            print(f"Transformation: OpenCC ({profile})")
        elif stage.name == "punctuation":
            print("Transformation: Punctuation")
        elif stage.name == "junk_cleaner":
            print("Transformation: Junk Cleaner")
        for warning in stage.warnings:
            print(f"WARNING: {stage.name}: {warning}", file=sys.stderr)


def execute(
    request: ConversionRequest,
    *,
    keep_intermediate: bool = False,
    intermediate: str | None = None,
) -> int:
    try:
        requested_encoding = None if request.policy.encoding == "auto" else request.policy.encoding
        lines, encoding = read_lines(request.source, requested_encoding)
        lines = [normalize_line(line) for line in lines]
        lines, audit = _run_transformations(
            lines,
            request.policy.transformations,
            full_source=request.policy.full_source,
        )
        result = parse_lines(
            lines,
            title=request.book_metadata.title,
            author=request.book_metadata.author,
            language=request.book_metadata.language,
            cover=request.book_metadata.cover,
            paragraph_mode=request.policy.parser.paragraph_mode,
        )
        report = validate_book(result.book, result.warnings)
        if report.errors:
            for error in report.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 2

        print(f"Encoding: {encoding}")
        print(f"Book: {result.book.title}")
        print(f"Author: {result.book.author}")
        print(f"Volumes: {len(result.book.volumes)}")
        print(f"Chapters: {result.book.chapter_count}")
        print(f"Paragraphs: {result.book.paragraph_count}")
        transformation_warning_count = sum(len(stage.warnings) for stage in audit)
        print(f"Warnings: {len(result.warnings) + transformation_warning_count}")
        _print_transform_audit(audit)
        for warning in result.warnings:
            where = f" at line {warning.line}" if warning.line else ""
            print(f"WARNING: {warning.message}{where}", file=sys.stderr)

        if keep_intermediate:
            intermediate_path = Path(
                intermediate or Path(request.source).with_suffix("").name + ".intermediate"
            )
            write_intermediate(result.book, intermediate_path, transformations=audit)
            print(f"Intermediate: {intermediate_path}")

        render(result.book, request.destination)
        epub_errors = validate_epub(request.destination)
        if epub_errors:
            for error in epub_errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 3
        print(f"EPUB: {request.destination}")
        return 0
    except TransformationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"ERROR: required executable or file not found: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

from __future__ import annotations

import argparse
import sys

from .cli_adapter import namespace_to_inputs
from .configuration_resolver import resolve_conversion_request
from .execution import ExecutionResult, execute
from .transforms import OpenCCTransformer
from .validator import run_epubcheck, validate_epub


def _report_execution(result: ExecutionResult) -> None:
    book_summary = getattr(result, "book_summary", {})
    warnings = getattr(result, "warnings", [])
    audit = getattr(result, "audit", [])
    validation = getattr(result, "validation", None)
    validation_warnings = getattr(validation, "warnings", []) if validation else []
    errors = getattr(result, "errors", [])
    intermediate_path = getattr(result, "intermediate_path", None)
    epub_path = getattr(result, "epub_path", None)
    return_code = getattr(result, "return_code", 1)
    encoding = getattr(result, "encoding", "")

    if book_summary:
        print(f"Encoding: {encoding}")
        print(f"Book: {book_summary['title']}")
        print(f"Author: {book_summary['author']}")
        print(f"Volumes: {book_summary['volumes']}")
        print(f"Chapters: {book_summary['chapters']}")
        print(f"Paragraphs: {book_summary['paragraphs']}")
        print(f"Warnings: {len(warnings)}")

    for stage in audit:
        if stage.name == "opencc":
            print(f"Transformation: OpenCC ({stage.metadata.get('profile', 'unknown')})")
        elif stage.name == "punctuation":
            print("Transformation: Punctuation")
        elif stage.name == "junk_cleaner":
            print("Transformation: Junk Cleaner")
        for warning in stage.warnings:
            print(f"WARNING: {stage.name}: {warning}", file=sys.stderr)

    for warning in validation_warnings:
        where = f" at line {warning.line}" if warning.line else ""
        print(f"WARNING: {warning.message}{where}", file=sys.stderr)

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if intermediate_path is not None:
        print(f"Intermediate: {intermediate_path}")
    if epub_path is not None and return_code == 0:
        print(f"EPUB: {epub_path}")


def build(request, *, keep_intermediate=False, intermediate=None):
    """Execute a resolved conversion request and report its structured result."""
    result = execute(
        request,
        keep_intermediate=keep_intermediate,
        intermediate=intermediate,
    )
    _report_execution(result)
    return result.return_code


def validate(args: argparse.Namespace) -> int:
    errors = validate_epub(args.epub)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    require_epubcheck = getattr(args, "require_epubcheck", False)
    epubcheck = run_epubcheck(args.epub, required=require_epubcheck)
    if not epubcheck.ok:
        for error in epubcheck.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.epub}")
    if not epubcheck.available:
        print("WARNING: EPUBCheck executable not found; external validation skipped.", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="novel-epub")
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build", help="parse TXT and build EPUB")
    build_parser.add_argument("input")
    build_parser.add_argument("-o", "--output")
    build_parser.add_argument("-t", "--title", required=True)
    build_parser.add_argument("-a", "--author", required=True)
    build_parser.add_argument("--lang")
    build_parser.add_argument("--cover")
    build_parser.add_argument("--encoding")
    build_parser.add_argument("--keep-intermediate", action="store_true")
    build_parser.add_argument("--intermediate")
    build_parser.add_argument(
        "--opencc-profile",
        choices=OpenCCTransformer.available_profiles(),
    )
    build_parser.add_argument("--no-opencc", dest="opencc", action="store_false", default=None)
    build_parser.add_argument("--no-punctuation", dest="punctuation", action="store_false", default=None)
    build_parser.add_argument("--full-source", action="store_true", default=None)
    build_parser.add_argument(
        "--paragraph-mode",
        choices=("wrapped", "line"),
        help="paragraph boundary semantics: blank-line wrapped paragraphs or one source line per paragraph",
    )

    validate_parser = sub.add_parser("validate", help="validate an EPUB archive")
    validate_parser.add_argument("epub")
    validate_parser.add_argument(
        "--require-epubcheck",
        action="store_true",
        help="fail if EPUBCheck is unavailable or reports validation errors",
    )
    validate_parser.set_defaults(func=validate)
    args = parser.parse_args()
    if args.command == "build":
        cli_inputs = namespace_to_inputs(args)
        request = resolve_conversion_request(cli_inputs)
        return build(
            request,
            keep_intermediate=args.keep_intermediate,
            intermediate=args.intermediate,
        )
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

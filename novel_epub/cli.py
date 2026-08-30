from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .intermediate import write_intermediate
from .normalize import read_lines
from .parser import parse_lines
from .renderers.pandoc import render
from .validator import run_epubcheck, validate_book, validate_epub


def build(args: argparse.Namespace) -> int:
    try:
        lines, encoding = read_lines(args.input, args.encoding)
        result = parse_lines(
            lines,
            title=args.title,
            author=args.author,
            language=args.lang,
            cover=args.cover,
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
        print(f"Warnings: {len(result.warnings)}")
        for warning in result.warnings:
            where = f" at line {warning.line}" if warning.line else ""
            print(f"WARNING: {warning.message}{where}", file=sys.stderr)

        if args.keep_intermediate:
            intermediate = Path(args.intermediate or Path(args.input).with_suffix("").name + ".intermediate")
            write_intermediate(result.book, intermediate)
            print(f"Intermediate: {intermediate}")

        output = Path(args.output) if args.output else Path(args.input).with_name(
            f"{args.title}_{args.author}.epub"
        )
        render(result.book, output)
        epub_errors = validate_epub(output)
        if epub_errors:
            for error in epub_errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 3
        print(f"EPUB: {output}")
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"ERROR: required executable or file not found: {exc}", file=sys.stderr)
        return 1


def validate(args: argparse.Namespace) -> int:
    errors = validate_epub(args.epub)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    epubcheck = run_epubcheck(args.epub)
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
    build_parser.add_argument("--lang", default="zh-CN")
    build_parser.add_argument("--cover")
    build_parser.add_argument("--encoding")
    build_parser.add_argument("--keep-intermediate", action="store_true")
    build_parser.add_argument("--intermediate")
    build_parser.set_defaults(func=build)

    validate_parser = sub.add_parser("validate", help="validate an EPUB archive")
    validate_parser.add_argument("epub")
    validate_parser.set_defaults(func=validate)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

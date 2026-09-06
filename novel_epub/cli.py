from __future__ import annotations

import argparse
import sys

from .cli_adapter import namespace_to_inputs
from .configuration_resolver import resolve_conversion_request
from .execution import execute
from .transforms import OpenCCTransformer
from .validator import run_epubcheck, validate_epub


def build(request, *, keep_intermediate=False, intermediate=None):
    """Execute a resolved conversion request."""
    return execute(
        request,
        keep_intermediate=keep_intermediate,
        intermediate=intermediate,
    )


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
    validate_parser.set_defaults(func=validate)
    args = parser.parse_args()
    if args.command == "build":
        request = resolve_conversion_request(namespace_to_inputs(args))
        return build(
            request,
            keep_intermediate=args.keep_intermediate,
            intermediate=args.intermediate,
        )
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

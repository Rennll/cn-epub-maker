"""Compatibility facade for the legacy validator API."""

import shutil
import subprocess

from .validation.book import ValidationReport, validate_book
from .validation.epub import validate_epub as _validate_epub
from .validation.epubcheck import EpubCheckResult, run_epubcheck as _run_epubcheck


def validate_epub(path):
    """Return EPUB validation errors using the legacy list-based contract."""
    return _validate_epub(path).errors


def run_epubcheck(path, *, required=False):
    """Run EPUBCheck while preserving legacy monkeypatchable dependencies."""
    return _run_epubcheck(
        path,
        required=required,
        which=shutil.which,
        runner=subprocess.run,
    )


__all__ = [
    "EpubCheckResult",
    "ValidationReport",
    "run_epubcheck",
    "validate_book",
    "validate_epub",
]

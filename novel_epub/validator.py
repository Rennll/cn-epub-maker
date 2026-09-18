"""Compatibility facade for the split validation modules.

Use ``novel_epub.validation`` for new imports.
"""

from .validation.book import ValidationReport, validate_book
from .validation.epub import validate_epub
from .validation.epubcheck import EpubCheckResult, run_epubcheck

__all__ = [
    "EpubCheckResult",
    "ValidationReport",
    "run_epubcheck",
    "validate_book",
    "validate_epub",
]

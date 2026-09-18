from __future__ import annotations

import mimetypes
import re
import subprocess
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

from ..models import Book, Chapter, Paragraph, ParagraphBoundary
from .epub import EpubPackageBuilder

CSS = """@charset "UTF-8";
body { font-size: 1em; line-height: 1.7; margin: 1em; text-align: left; }
p { text-indent: 2em; margin: 0; padding: 0; }
p.paragraph-expanded { margin-top: 1.5em; }
p.paragraph-scene-break { margin-top: 2.5em; }
h1 { text-align: center; break-before: page; page-break-before: always; }
"""

_MARKDOWN_CHARS = re.compile(r"([\\`*{}\[\]()#+.!_>|~\-=\^$:])")
_P_OPEN = re.compile(r"<p(\s[^>]*)?>")
_NS_EPUB = "http://www.idpf.org/2007/ops"
_NS_OPF = "http://www.idpf.org/2007/opf"
_NS_DC = "http://purl.org/dc/elements/1.1/"


def _iter_chapters(book: Book):
    for volume in book.volumes:
        yield from ((volume, chapter) for chapter in volume.chapters)
    yield from ((None, chapter) for chapter in book.chapters)


class RenderingError(Exception):
    """Fatal renderer failure after the book model has been validated."""


def _run_pandoc(args: list[str]) -> None:
    try:
        subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        suffix = f": {detail}" if detail else ""
        raise RenderingError(f"Pandoc rendering failed with exit code {exc.returncode}{suffix}") from exc


def _escape_markdown(text: str) -> str:
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return "  \n".join(_MARKDOWN_CHARS.sub(r"\\\1", line) for line in escaped.split("\n"))


def _chapter_heading(chapter: Chapter, level: int = 1) -> str:
    text = f"{chapter.label} {chapter.title}".rstrip()
    return f"{'#' * level} {_escape_markdown(text)}"


def _chapter_markdown(chapter: Chapter) -> str:
    lines = [_chapter_heading(chapter), ""]
    for paragraph in chapter.paragraphs:
        lines.extend([_escape_markdown(paragraph.text), ""])
    return "\n".join(lines).rstrip() + "\n"


def _preamble_markdown(book: Book) -> str:
    lines: list[str] = []
    for paragraph in book.preamble:
        lines.extend([_escape_markdown(paragraph.text), ""])
    return "\n".join(lines).rstrip() + "\n"


def _markdown(book: Book) -> str:
    lines: list[str] = []
    for paragraph in book.preamble:
        lines.extend([_escape_markdown(paragraph.text), ""])
    if book.volumes:
        for volume in book.volumes:
            volume_text = f"{volume.label} {volume.title}".rstrip()
            lines.extend([f"# {_escape_markdown(volume_text)}", ""])
            for chapter in volume.chapters:
                lines.extend([_chapter_heading(chapter, 2), ""])
                for paragraph in chapter.paragraphs:
                    lines.extend([_escape_markdown(paragraph.text), ""])
    for chapter in book.chapters:
        lines.extend([_chapter_heading(chapter), ""])
        for paragraph in chapter.paragraphs:
            lines.extend([_escape_markdown(paragraph.text), ""])
    return "\n".join(lines).rstrip() + "\n"


def render(book: Book, output: str | Path) -> Path:
    """Render chapters with Pandoc, then delegate EPUB assembly."""
    _validate_book(book)
    output = Path(output)
    with TemporaryDirectory(prefix="novel-epub-") as tmp:
        root = Path(tmp)
        chapter_dir = root / "chapters"
        chapter_dir.mkdir()
        chapter_files: list[tuple[Chapter, Path]] = []
        for _volume, chapter in _iter_chapters(book):
            destination = chapter_dir / f"ch{chapter.sequence:06d}.xhtml"
            _pandoc_chapter(chapter, destination, book.language)
            chapter_files.append((chapter, destination))
        preamble_file = None
        if book.preamble:
            preamble_file = root / "preamble.xhtml"
            _pandoc_preamble(book, preamble_file)
        EpubPackageBuilder().build(book, output, chapter_files, preamble_file)
    return output

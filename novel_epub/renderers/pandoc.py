from __future__ import annotations

import mimetypes
import os
import re
import subprocess
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

from ..models import Book, Chapter, Paragraph, ParagraphBoundary

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


def _iter_chapters(book: Book):
    for volume in book.volumes:
        yield from ((volume, chapter) for chapter in volume.chapters)
    yield from ((None, chapter) for chapter in book.chapters)


def _validate_book(book: Book) -> None:
    sequences = [chapter.sequence for _volume, chapter in _iter_chapters(book)]
    if len(sequences) != len(set(sequences)):
        raise ValueError("duplicate chapter sequence")
    if book.cover:
        cover = Path(book.cover)
        if not cover.is_file():
            raise FileNotFoundError(f"cover file not found: {cover}")
        media_type = mimetypes.guess_type(cover.name)[0]
        if media_type not in {"image/jpeg", "image/png", "image/gif", "image/webp"}:
            raise ValueError(f"unsupported cover media type: {cover.name}")


def _paragraph_class(boundary: ParagraphBoundary) -> str:
    if boundary is ParagraphBoundary.EXPANDED:
        return ' class="paragraph-expanded"'
    if boundary is ParagraphBoundary.SCENE_BREAK:
        return ' class="paragraph-scene-break"'
    return ""


def _apply_paragraph_boundaries(body: str, paragraphs: list[Paragraph]) -> str:
    index = 0
    def replace(match: re.Match[str]) -> str:
        nonlocal index
        if index >= len(paragraphs):
            return match.group(0)
        boundary = paragraphs[index].boundary
        index += 1
        return f"<p{_paragraph_class(boundary)}>"
    return _P_OPEN.sub(replace, body)


def _pandoc_chapter(chapter: Chapter, destination: Path, language: str) -> None:
    source = destination.with_suffix(".md")
    fragment = destination.with_suffix(".html")
    source.write_text(_chapter_markdown(chapter), encoding="utf-8")
    _run_pandoc(["pandoc", str(source), "--from=markdown", "--to=html5", "--output", str(fragment)])
    body = _apply_paragraph_boundaries(fragment.read_text(encoding="utf-8").strip(), chapter.paragraphs)
    language = escape(language)
    chapter_title = escape(f"{chapter.label} {chapter.title}".rstrip())
    destination.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
        f'<html xmlns="http://www.w3.org/1999/xhtml" lang="{language}" xml:lang="{language}">\n'
        '<head>\n<meta charset="utf-8" />\n'
        f'<title>{chapter_title}</title>\n<link rel="stylesheet" type="text/css" href="../styles/stylesheet.css" />\n'
        '</head>\n<body>\n' + body + '\n</body>\n</html>\n', encoding="utf-8")


def _pandoc_preamble(book: Book, destination: Path) -> None:
    source = destination.with_suffix(".md")
    fragment = destination.with_suffix(".html")
    source.write_text(_preamble_markdown(book), encoding="utf-8")
    _run_pandoc(["pandoc", str(source), "--from=markdown", "--to=html5", "--output", str(fragment)])
    body = _apply_paragraph_boundaries(fragment.read_text(encoding="utf-8").strip(), book.preamble)
    language = escape(book.language)
    destination.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
        f'<html xmlns="http://www.w3.org/1999/xhtml" lang="{language}" xml:lang="{language}">\n'
        '<head>\n<meta charset="utf-8" />\n'
        f'<title>{escape(book.title)}</title>\n<link rel="stylesheet" type="text/css" href="../styles/stylesheet.css" />\n'
        '</head>\n<body>\n' + body + '\n</body>\n</html>\n', encoding="utf-8")


from .epub import EpubPackageBuilder

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

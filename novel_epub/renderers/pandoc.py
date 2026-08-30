from __future__ import annotations

import mimetypes
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from ..models import Book, Chapter

CSS = """@charset "UTF-8";
body { font-size: 1em; line-height: 1.8; margin: 1em; text-align: justify; }
p { text-indent: 2em; margin: 0; padding: 0; }
h1 { text-align: center; }
"""

_MARKDOWN_CHARS = re.compile(r"([\\`*{}\[\]()#+.!_>|~-])")


def _escape_markdown(text: str) -> str:
    return "\n".join(_MARKDOWN_CHARS.sub(r"\\\1", line) for line in text.split("\n"))


def _chapter_markdown(chapter: Chapter) -> str:
    lines = [f"# {chapter.label} {chapter.title}".rstrip(), ""]
    for paragraph in chapter.paragraphs:
        lines.extend([_escape_markdown(paragraph.text), ""])
    return "\n".join(lines).rstrip() + "\n"


def _markdown(book: Book) -> str:
    """Render the model as a debug-friendly single Markdown document."""
    lines: list[str] = []
    if book.volumes:
        for volume in book.volumes:
            lines.extend([f"# {volume.label} {volume.title}".rstrip(), ""])
            for chapter in volume.chapters:
                lines.extend(_chapter_markdown(chapter).rstrip().splitlines())
                lines.append("")
    for chapter in book.chapters:
        lines.extend(_chapter_markdown(chapter).rstrip().splitlines())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _pandoc_chapter(chapter: Chapter, destination: Path, css: Path) -> None:
    source = destination.with_suffix(".md")
    source.write_text(_chapter_markdown(chapter), encoding="utf-8")
    subprocess.run(
        [
            "pandoc", str(source), "-o", str(destination),
            "--css", str(css), "--to=epub3",
            "--metadata", f"title={chapter.label} {chapter.title}".rstrip(),
            "--metadata", f"pagetitle={chapter.label} {chapter.title}".rstrip(),
        ],
        check=True,
    )


def _iter_chapters(book: Book):
    if book.volumes:
        for volume in book.volumes:
            for chapter in volume.chapters:
                yield volume, chapter
    else:
        for chapter in book.chapters:
            yield None, chapter


def render(book: Book, output: str | Path) -> Path:
    """Convert each Chapter independently; EPUB assembly follows separately."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="novel-epub-") as tmp:
        root = Path(tmp)
        css = root / "style.css"
        css.write_text(CSS, encoding="utf-8")
        chapter_dir = root / "chapters"
        chapter_dir.mkdir()
        for _volume, chapter in _iter_chapters(book):
            destination = chapter_dir / f"ch{chapter.sequence:06d}.xhtml"
            _pandoc_chapter(chapter, destination, css)
        # EPUB packaging/navigation is intentionally the next renderer step.
        raise NotImplementedError("native EPUB assembly is the next renderer step")

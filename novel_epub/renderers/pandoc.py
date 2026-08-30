from __future__ import annotations

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from ..models import Book

CSS = """@charset "UTF-8";
body {
  font-size: 1em;
  line-height: 1.8;
  margin: 1em;
  text-align: justify;
}
p { text-indent: 2em; margin: 0; padding: 0; }
h1, h2 { text-align: center; }
"""


def _markdown(book: Book) -> str:
    lines: list[str] = []
    for volume in book.volumes:
        # Volume is a navigation grouping. Pandoc heading hierarchy is used
        # here; chapter headings are the split level/content documents.
        lines.append(f"# {volume.label} {volume.title}".rstrip())
        lines.append("")
        for chapter in volume.chapters:
            lines.extend(_chapter_markdown(chapter))
    for chapter in book.chapters:
        lines.extend(_chapter_markdown(chapter))
    return "\n".join(lines).rstrip() + "\n"


def _chapter_markdown(chapter) -> list[str]:
    lines = [f"## {chapter.label} {chapter.title}".rstrip(), ""]
    for paragraph in chapter.paragraphs:
        lines.extend([paragraph.text, ""])
    return lines


def render(book: Book, output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="novel-epub-") as tmp:
        root = Path(tmp)
        md = root / "book.md"
        css = root / "style.css"
        md.write_text(_markdown(book), encoding="utf-8")
        css.write_text(CSS, encoding="utf-8")

        cmd = [
            "pandoc", str(md), "-o", str(output),
            "--toc", "--toc-depth=2", "--split-level=2",
            "--css", str(css),
            "--metadata", f"title={book.title}",
            "--metadata", f"author={book.author}",
            "--metadata", f"lang={book.language}",
        ]
        if book.cover:
            cover = Path(book.cover)
            if cover.is_file():
                cmd += ["--epub-cover-image", str(cover)]

        subprocess.run(cmd, check=True)
    return output

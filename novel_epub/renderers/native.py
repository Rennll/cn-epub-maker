from __future__ import annotations

from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

from ..models import Book, Chapter, Paragraph, ParagraphBoundary
from .epub import EpubPackageBuilder, _iter_chapters


class NativeRenderingError(Exception):
    """Fatal native renderer failure."""



class NativeRenderer:
    """Render the semantic Book model directly to minimal EPUB XHTML."""

    def render(self, book: Book, output: str | Path) -> Path:
        self._validate_book(book)
        output = Path(output)
        with TemporaryDirectory(prefix="novel-epub-native-") as tmp:
            root = Path(tmp)
            chapter_dir = root / "chapters"
            chapter_dir.mkdir()
            chapter_files: list[tuple[Chapter, Path]] = []

            for _volume, chapter in _iter_chapters(book):
                destination = chapter_dir / f"ch{chapter.sequence:06d}.xhtml"
                self._render_chapter(book, chapter, destination)
                chapter_files.append((chapter, destination))

            preamble_file = None
            if book.preamble:
                preamble_file = root / "preamble.xhtml"
                self._render_preamble(book, preamble_file)

            EpubPackageBuilder().build(
                book,
                output,
                chapter_files,
                preamble_file,
            )
        return output

    @staticmethod
    def _validate_book(book: Book) -> None:
        sequences = [chapter.sequence for _volume, chapter in _iter_chapters(book)]
        if len(sequences) != len(set(sequences)):
            raise NativeRenderingError("duplicate chapter sequence")
        if not book.title.strip():
            raise NativeRenderingError("book title is empty")
        if not book.author.strip():
            raise NativeRenderingError("author is empty")
        if not sequences:
            raise NativeRenderingError("book contains no chapters")
        if book.cover and not Path(book.cover).is_file():
            raise FileNotFoundError(f"cover file not found: {book.cover}")

    @staticmethod
    def _render_chapter(book: Book, chapter: Chapter, destination: Path) -> None:
        title = escape(f"{chapter.label} {chapter.title}".rstrip())
        body = f"<h1>{title}</h1>\n" + "".join(NativeRenderer._paragraph(paragraph) for paragraph in chapter.paragraphs)
        destination.write_text(
            NativeRenderer._document(book.language, title, body),
            encoding="utf-8",
        )

    @staticmethod
    def _render_preamble(book: Book, destination: Path) -> None:
        title = escape(book.title)
        body = f"<h1>{title}</h1>\n" + "".join(NativeRenderer._paragraph(paragraph) for paragraph in book.preamble)
        destination.write_text(
            NativeRenderer._document(book.language, title, body),
            encoding="utf-8",
        )

    @staticmethod
    def _paragraph(paragraph: Paragraph) -> str:
        classes = {
            ParagraphBoundary.EXPANDED: "paragraph-expanded",
            ParagraphBoundary.SCENE_BREAK: "paragraph-scene-break",
        }
        class_name = classes.get(paragraph.boundary)
        class_attr = f' class="{class_name}"' if class_name else ""
        text = escape(paragraph.text).replace("\n", "<br />\n")
        return f"<p{class_attr}>{text}</p>\n"

    @staticmethod
    def _document(language: str, title: str, body: str) -> str:
        language = escape(language)
        return (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" lang="{language}" xml:lang="{language}">\n'
            '<head>\n'
            '<meta charset="utf-8" />\n'
            f'<title>{title}</title>\n'
            '<link rel="stylesheet" type="text/css" href="../styles/stylesheet.css" />\n'
            '</head>\n'
            f'<body>\n{body}</body>\n'
            '</html>\n'
        )

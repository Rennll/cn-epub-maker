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

_MARKDOWN_CHARS = re.compile(r"([\\`*{}\[\]()#+.!_>|~-])")
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
    return f"{'#' * level} {chapter.label} {chapter.title}".rstrip()


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
            lines.extend([f"# {volume.label} {volume.title}".rstrip(), ""])
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
    _run_pandoc(["pandoc", str(source), "--from=markdown-smart", "--to=html5", "--output", str(fragment)])
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
    _run_pandoc(["pandoc", str(source), "--from=markdown-smart", "--to=html5", "--output", str(fragment)])
    body = _apply_paragraph_boundaries(fragment.read_text(encoding="utf-8").strip(), book.preamble)
    language = escape(book.language)
    destination.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
        f'<html xmlns="http://www.w3.org/1999/xhtml" lang="{language}" xml:lang="{language}">\n'
        '<head>\n<meta charset="utf-8" />\n'
        f'<title>{escape(book.title)}</title>\n<link rel="stylesheet" type="text/css" href="../styles/stylesheet.css" />\n'
        '</head>\n<body>\n' + body + '\n</body>\n</html>\n', encoding="utf-8")


def _nav_xhtml(book: Book, chapter_paths: dict[int, str]) -> str:
    def chapter_li(chapter: Chapter) -> str:
        label = escape(f"{chapter.label} {chapter.title}".rstrip())
        return f'<li><a href="{chapter_paths[chapter.sequence]}">{label}</a></li>'
    groups: list[str] = []
    if book.preamble:
        groups.append('<li><a href="text/preamble.xhtml">前言</a></li>')
    if book.volumes:
        for volume in book.volumes:
            label = escape(f"{volume.label} {volume.title}".rstrip())
            children = "".join(chapter_li(ch) for ch in volume.chapters)
            groups.append(f"<li><span>{label}</span><ol>{children}</ol></li>")
    if book.chapters:
        groups.extend(chapter_li(ch) for ch in book.chapters)
    title = escape(book.title)
    language = escape(book.language)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="{_NS_EPUB}" lang="{language}" xml:lang="{language}">
<head><meta charset="utf-8" /><title>{title}</title></head>
<body>
<nav epub:type="toc" id="toc"><h1>{title}</h1><ol>{''.join(groups)}</ol></nav>
</body>
</html>
'''


def _content_opf(book: Book, chapter_paths: dict[int, str], identifier: str, cover_name: str | None, has_preamble: bool = False) -> str:
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '<item id="css" href="styles/stylesheet.css" media-type="text/css" />',
    ]
    spine: list[str] = []
    if has_preamble:
        manifest.append('<item id="preamble" href="text/preamble.xhtml" media-type="application/xhtml+xml" />')
        spine.append('<itemref idref="preamble" />')
    for index, (_volume, chapter) in enumerate(_iter_chapters(book), start=1):
        item_id = f"ch{index:06d}"
        href = chapter_paths[chapter.sequence]
        manifest.append(f'<item id="{item_id}" href="{href}" media-type="application/xhtml+xml" />')
        spine.append(f'<itemref idref="{item_id}" />')
    cover_meta = ""
    if cover_name:
        media_type = mimetypes.guess_type(cover_name)[0]
        manifest.append(f'<item id="cover-image" href="images/{escape(Path(cover_name).name)}" media-type="{media_type}" properties="cover-image" />')
        cover_meta = '<meta name="cover" content="cover-image" />'
    modified = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="{_NS_OPF}" version="3.0" unique-identifier="pub-id" xml:lang="{escape(book.language)}">
<metadata xmlns:dc="{_NS_DC}">
<dc:identifier id="pub-id">urn:uuid:{identifier}</dc:identifier>
<dc:title>{escape(book.title)}</dc:title>
<dc:creator>{escape(book.author)}</dc:creator>
<dc:language>{escape(book.language)}</dc:language>
<meta property="dcterms:modified">{modified}</meta>
{cover_meta}
</metadata>
<manifest>{''.join(manifest)}</manifest>
<spine>{''.join(spine)}</spine>
</package>
'''


def _write_epub(book: Book, output: Path, chapter_files: list[tuple[Chapter, Path]], preamble_file: Path | None = None) -> None:
    identifier = str(uuid.uuid4())
    chapter_paths = {chapter.sequence: f"text/ch{index:06d}.xhtml" for index, (chapter, _source) in enumerate(chapter_files, start=1)}
    preamble_manifest = '<item id="preamble" href="text/preamble.xhtml" media-type="application/xhtml+xml" />' if preamble_file else ''
    with zipfile.ZipFile(output, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml" /></rootfiles></container>')
        zf.writestr("EPUB/nav.xhtml", _nav_xhtml(book, chapter_paths))
        zf.writestr("EPUB/styles/stylesheet.css", CSS)
        if preamble_file:
            zf.write(preamble_file, "EPUB/text/preamble.xhtml")
        for chapter, source in chapter_files:
            zf.write(source, f"EPUB/text/ch{chapter_paths[chapter.sequence].split('ch')[-1]}")
        zf.writestr("EPUB/content.opf", _content_opf(book, chapter_paths, identifier, book.cover, bool(preamble_file)))
        if book.cover:
            zf.write(book.cover, f"EPUB/images/{Path(book.cover).name}")


def render(book: Book, output: Path) -> None:
    _validate_book(book)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="cn-epub-render-") as temp:
        temp_dir = Path(temp)
        chapter_files: list[tuple[Chapter, Path]] = []
        for index, (_volume, chapter) in enumerate(_iter_chapters(book), start=1):
            destination = temp_dir / f"ch{index:06d}.xhtml"
            _pandoc_chapter(chapter, destination, book.language)
            chapter_files.append((chapter, destination))
        preamble_file = None
        if book.preamble:
            preamble_file = temp_dir / "preamble.xhtml"
            _pandoc_preamble(book, preamble_file)
        staging = output.with_suffix(output.suffix + ".tmp")
        try:
            _write_epub(book, staging, chapter_files, preamble_file)
            os.replace(staging, output)
        except OSError:
            if staging.exists():
                staging.unlink()
            raise

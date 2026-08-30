from __future__ import annotations

import mimetypes
import re
import subprocess
import uuid
import zipfile
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

from ..models import Book, Chapter

CSS = """@charset "UTF-8";
body { font-size: 1em; line-height: 1.8; margin: 1em; text-align: justify; }
p { text-indent: 2em; margin: 0; padding: 0; }
h1 { text-align: center; }
"""

_MARKDOWN_CHARS = re.compile(r"([\\`*{}\[\]()#+.!_>|~-])")
_NS_EPUB = "http://www.idpf.org/2007/ops"
_NS_OPF = "http://www.idpf.org/2007/opf"
_NS_DC = "http://purl.org/dc/elements/1.1/"


def _escape_markdown(text: str) -> str:
    return "\n".join(_MARKDOWN_CHARS.sub(r"\\\1", line) for line in text.split("\n"))


def _chapter_heading(chapter: Chapter, level: int = 1) -> str:
    return f"{'#' * level} {chapter.label} {chapter.title}".rstrip()


def _chapter_markdown(chapter: Chapter) -> str:
    lines = [_chapter_heading(chapter), ""]
    for paragraph in chapter.paragraphs:
        lines.extend([_escape_markdown(paragraph.text), ""])
    return "\n".join(lines).rstrip() + "\n"


def _markdown(book: Book) -> str:
    """Render the model as a debug-friendly whole-book Markdown document."""
    lines: list[str] = []
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


def _pandoc_chapter(chapter: Chapter, destination: Path, language: str) -> None:
    source = destination.with_suffix(".md")
    fragment = destination.with_suffix(".html")
    source.write_text(_chapter_markdown(chapter), encoding="utf-8")
    subprocess.run(
        ["pandoc", str(source), "--from=markdown", "--to=html5", "--output", str(fragment)],
        check=True,
    )
    body = fragment.read_text(encoding="utf-8").strip()
    chapter_title = escape(f"{chapter.label} {chapter.title}".rstrip())
    language = escape(language)
    xhtml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n'
        f'<html xmlns="http://www.w3.org/1999/xhtml" lang="{language}" xml:lang="{language}">\n'
        "<head>\n"
        '<meta charset="utf-8" />\n'
        f"<title>{chapter_title}</title>\n"
        '<link rel="stylesheet" type="text/css" href="../styles/stylesheet.css" />\n'
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n</html>\n"
    )
    destination.write_text(xhtml, encoding="utf-8")


def _nav_xhtml(book: Book, chapter_paths: dict[int, str]) -> str:
    def chapter_li(chapter: Chapter) -> str:
        label = escape(f"{chapter.label} {chapter.title}".rstrip())
        return f'<li><a href="{chapter_paths[chapter.sequence]}">{label}</a></li>'

    groups: list[str] = []
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


def _content_opf(book: Book, chapter_paths: dict[int, str], identifier: str, cover_name: str | None) -> str:
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '<item id="css" href="styles/stylesheet.css" media-type="text/css" />',
    ]
    spine: list[str] = []
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

    return f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="{_NS_OPF}" version="3.0" unique-identifier="pub-id" xml:lang="{escape(book.language)}">
<metadata xmlns:dc="{_NS_DC}">
<dc:identifier id="pub-id">urn:uuid:{identifier}</dc:identifier>
<dc:title>{escape(book.title)}</dc:title>
<dc:creator>{escape(book.author)}</dc:creator>
<dc:language>{escape(book.language)}</dc:language>
{cover_meta}
</metadata>
<manifest>{''.join(manifest)}</manifest>
<spine>{''.join(spine)}</spine>
</package>
'''


def _write_epub(book: Book, output: Path, chapter_files: list[tuple[Chapter, Path]]) -> None:
    identifier = str(uuid.uuid4())
    chapter_paths = {chapter.sequence: f"text/ch{index:06d}.xhtml" for index, (chapter, _source) in enumerate(chapter_files, start=1)}
    cover_name = Path(book.cover).name if book.cover else None
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml" /></rootfiles>
</container>
'''
    with zipfile.ZipFile(output, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("EPUB/nav.xhtml", _nav_xhtml(book, chapter_paths))
        zf.writestr("EPUB/styles/stylesheet.css", CSS)
        for chapter, source in chapter_files:
            zf.writestr(f"EPUB/{chapter_paths[chapter.sequence]}", source.read_bytes())
        zf.writestr("EPUB/content.opf", _content_opf(book, chapter_paths, identifier, cover_name))
        if book.cover:
            cover = Path(book.cover)
            zf.write(cover, f"EPUB/images/{cover.name}")


def render(book: Book, output: str | Path) -> Path:
    """Render chapters independently with Pandoc, then assemble a native EPUB."""
    _validate_book(book)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="novel-epub-") as tmp:
        root = Path(tmp)
        chapter_dir = root / "chapters"
        chapter_dir.mkdir()
        chapter_files: list[tuple[Chapter, Path]] = []
        for _volume, chapter in _iter_chapters(book):
            destination = chapter_dir / f"ch{chapter.sequence:06d}.xhtml"
            _pandoc_chapter(chapter, destination, book.language)
            chapter_files.append((chapter, destination))
        _write_epub(book, output, chapter_files)
    return output

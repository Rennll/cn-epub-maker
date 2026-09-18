from __future__ import annotations

import mimetypes
import os
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from ..models import Book, Chapter

_NS_EPUB = "http://www.idpf.org/2007/ops"
_NS_OPF = "http://www.idpf.org/2007/opf"
_NS_DC = "http://purl.org/dc/elements/1.1/"

CSS = """@charset "UTF-8";
body { font-size: 1em; line-height: 1.7; margin: 1em; text-align: left; }
p { text-indent: 2em; margin: 0; padding: 0; }
p.paragraph-expanded { margin-top: 1.5em; }
p.paragraph-scene-break { margin-top: 2.5em; }
h1 { text-align: center; break-before: page; page-break-before: always; }
"""


class EpubPackagingError(Exception):
    """Fatal EPUB package construction failure."""


def _iter_chapters(book: Book):
    for volume in book.volumes:
        yield from ((volume, chapter) for chapter in volume.chapters)
    yield from ((None, chapter) for chapter in book.chapters)


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
        groups.extend(chapter_li(chapter) for chapter in book.chapters)

    title = escape(book.title)
    language = escape(book.language)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="{_NS_EPUB}" lang="{language}" xml:lang="{language}">
<head><meta charset="utf-8" /><title>{title}</title></head>
<body>
<nav epub:type="toc" id="toc"><h1>{title}</h1><ol>{''.join(groups)}</ol></nav></body>
</html>
'''


def _content_opf(
    book: Book,
    chapter_paths: dict[int, str],
    identifier: str,
    cover_name: str | None,
    has_preamble: bool = False,
) -> str:
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
        manifest.append(
            f'<item id="cover-image" href="images/{escape(Path(cover_name).name)}" '
            f'media-type="{media_type}" properties="cover-image" />'
        )
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


class EpubPackageBuilder:
    """Assemble rendered XHTML and resources into the project's EPUB package.

    This class does not invoke Pandoc or interpret Markdown.
    """

    def build(
        self,
        book: Book,
        output: str | Path,
        chapter_files: list[tuple[Chapter, Path]],
        preamble_file: Path | None = None,
    ) -> Path:
        output = Path(output)
        chapter_paths = {
            chapter.sequence: f"text/ch{index:06d}.xhtml"
            for index, (chapter, _source) in enumerate(chapter_files, start=1)
        }
        cover_name = Path(book.cover).name if book.cover else None
        container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml" /></rootfiles>
</container>
'''
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
        try:
            with os.fdopen(fd, "wb") as output_file:
                with zipfile.ZipFile(output_file, "w") as zf:
                    zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
                    zf.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
                    zf.writestr("EPUB/nav.xhtml", _nav_xhtml(book, chapter_paths), compress_type=zipfile.ZIP_DEFLATED)
                    zf.writestr("EPUB/styles/stylesheet.css", CSS, compress_type=zipfile.ZIP_DEFLATED)
                    if preamble_file:
                        zf.writestr("EPUB/text/preamble.xhtml", preamble_file.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
                    for chapter, source in chapter_files:
                        zf.writestr(
                            f"EPUB/{chapter_paths[chapter.sequence]}",
                            source.read_bytes(),
                            compress_type=zipfile.ZIP_DEFLATED,
                        )
                    zf.writestr(
                        "EPUB/content.opf",
                        _content_opf(book, chapter_paths, str(uuid.uuid4()), cover_name, bool(preamble_file)),
                        compress_type=zipfile.ZIP_DEFLATED,
                    )
                    if book.cover:
                        cover = Path(book.cover)
                        zf.write(cover, f"EPUB/images/{cover.name}", compress_type=zipfile.ZIP_DEFLATED)
        except BaseException:
            try:
                output.unlink()
            except FileNotFoundError:
                pass
            raise
        return output

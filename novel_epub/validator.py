from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from .models import Book
from .parser import WarningItem


@dataclass
class ValidationReport:
    errors: list[str]
    warnings: list[WarningItem]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_book(book: Book, warnings: list[WarningItem]) -> ValidationReport:
    errors: list[str] = []
    if not book.title.strip():
        errors.append("book title is empty")
    if not book.author.strip():
        errors.append("author is empty")
    if book.chapter_count == 0:
        errors.append("book contains no chapters")
    for chapter in book.iter_chapters():
        if not chapter.paragraphs:
            warnings.append(WarningItem("empty_chapter", 0, f"empty chapter: {chapter.label}"))
    return ValidationReport(errors, warnings)


_OPF_NS = "http://www.idpf.org/2007/opf"
_CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
_XHTML_NS = "http://www.w3.org/1999/xhtml"
_EPUB_NS = "http://www.idpf.org/2007/ops"


def _href_to_archive_path(base_path: str, href: str) -> str:
    return str((Path(base_path).parent / href.split("#", 1)[0]).as_posix())


def _validate_epub_structure(zf: ZipFile, errors: list[str]) -> None:
    names = set(zf.namelist())
    try:
        container_root = ET.fromstring(zf.read("META-INF/container.xml"))
    except KeyError:
        return
    except ET.ParseError as exc:
        errors.append(f"invalid container.xml: {exc}")
        return

    rootfile = container_root.find(f"{{{_CONTAINER_NS}}}rootfiles/{{{_CONTAINER_NS}}}rootfile")
    if rootfile is None or not rootfile.get("full-path"):
        errors.append("container rootfile missing")
        return
    opf_path = rootfile.get("full-path")
    if opf_path not in names:
        errors.append(f"container rootfile missing: {opf_path}")
        return

    try:
        opf_root = ET.fromstring(zf.read(opf_path))
    except ET.ParseError as exc:
        errors.append(f"invalid content.opf: {exc}")
        return

    manifest = opf_root.find(f"{{{_OPF_NS}}}manifest")
    spine = opf_root.find(f"{{{_OPF_NS}}}spine")
    if manifest is None:
        errors.append("OPF manifest missing")
        return
    if spine is None:
        errors.append("OPF spine missing")
        return

    items: dict[str, ET.Element] = {}
    for item in manifest.findall(f"{{{_OPF_NS}}}item"):
        item_id = item.get("id")
        href = item.get("href")
        if not item_id or not href:
            errors.append("manifest item missing id or href")
            continue
        items[item_id] = item
        target = _href_to_archive_path(opf_path, href)
        if target not in names:
            errors.append(f"manifest target missing: {target}")

    nav_items = [
        item for item in items.values()
        if "nav" in (item.get("properties") or "").split()
    ]
    if len(nav_items) != 1:
        errors.append("EPUB must contain exactly one nav manifest item")
    else:
        nav_path = _href_to_archive_path(opf_path, nav_items[0].get("href", ""))
        try:
            nav_root = ET.fromstring(zf.read(nav_path))
        except ET.ParseError as exc:
            errors.append(f"invalid nav.xhtml: {exc}")
        except KeyError:
            pass
        else:
            toc = None
            for nav in nav_root.findall(f".//{{{_XHTML_NS}}}nav"):
                if nav.get(f"{{{_EPUB_NS}}}type") == "toc":
                    toc = nav
                    break
            if toc is None:
                toc = nav_root.find(f".//{{{_XHTML_NS}}}nav")
            if toc is not None:
                for anchor in toc.findall(f".//{{{_XHTML_NS}}}a"):
                    href = anchor.get("href", "")
                    if not href or href.startswith("#"):
                        continue
                    target = _href_to_archive_path(nav_path, href)
                    if target not in names:
                        errors.append(f"nav target missing: {target}")

    for itemref in spine.findall(f"{{{_OPF_NS}}}itemref"):
        idref = itemref.get("idref")
        if not idref or idref not in items:
            errors.append(f"spine idref missing from manifest: {idref}")


def validate_epub(path: str | Path) -> list[str]:
    errors: list[str] = []
    path = Path(path)
    if not path.is_file():
        return [f"EPUB not found: {path}"]
    try:
        with ZipFile(path) as zf:
            names = zf.namelist()
            if not names or names[0] != "mimetype":
                errors.append("mimetype must be the first EPUB archive entry")
            elif zf.read("mimetype") != b"application/epub+zip":
                errors.append("invalid EPUB mimetype")
            if "META-INF/container.xml" not in names:
                errors.append("missing required EPUB file: META-INF/container.xml")
            else:
                _validate_epub_structure(zf, errors)
    except Exception as exc:
        errors.append(f"invalid EPUB archive: {exc}")
    return errors

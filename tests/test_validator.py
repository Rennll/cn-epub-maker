from pathlib import Path
from zipfile import ZipFile

from novel_epub.validator import validate_epub


def _write_epub(tmp_path: Path, *, container: str, opf: str, files: dict[str, str] | None = None) -> Path:
    path = tmp_path / "book.epub"
    with ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("EPUB/content.opf", opf)
        for name, content in (files or {}).items():
            zf.writestr(name, content)
    return path


CONTAINER = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml" /></rootfiles>
</container>
'''


NAV = '''<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <body><nav epub:type="toc"><a href="text/ch000001.xhtml">Chapter</a></nav></body>
</html>'''


def _opf(manifest: str, spine: str, metadata: str = "<dc:title>Book</dc:title>") -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">urn:uuid:test</dc:identifier>
    {metadata}
  </metadata>
  <manifest>{manifest}</manifest>
  <spine>{spine}</spine>
</package>
'''


def test_valid_epub_structure_passes(tmp_path: Path):
    opf = _opf(
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />'
        '<item id="css" href="styles/stylesheet.css" media-type="text/css" />'
        '<item id="ch1" href="text/ch000001.xhtml" media-type="application/xhtml+xml" />',
        '<itemref idref="ch1" />',
    )
    path = _write_epub(
        tmp_path,
        container=CONTAINER,
        opf=opf,
        files={
            "EPUB/nav.xhtml": NAV,
            "EPUB/styles/stylesheet.css": "body {}",
            "EPUB/text/ch000001.xhtml": "<html xmlns=\"http://www.w3.org/1999/xhtml\"><body><h1>Chapter</h1></body></html>",
        },
    )
    assert validate_epub(path) == []


def test_missing_opf_target_is_reported(tmp_path: Path):
    opf = _opf(
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />'
        '<item id="ch1" href="text/missing.xhtml" media-type="application/xhtml+xml" />',
        '<itemref idref="ch1" />',
    )
    path = _write_epub(
        tmp_path,
        container=CONTAINER,
        opf=opf,
        files={"EPUB/nav.xhtml": NAV},
    )
    errors = validate_epub(path)
    assert any("manifest target missing" in error for error in errors)


def test_spine_reference_must_exist_in_manifest(tmp_path: Path):
    opf = _opf(
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '<itemref idref="missing" />',
    )
    path = _write_epub(
        tmp_path,
        container=CONTAINER,
        opf=opf,
        files={"EPUB/nav.xhtml": NAV},
    )
    errors = validate_epub(path)
    assert any("spine idref missing from manifest" in error for error in errors)


def test_nav_target_must_exist(tmp_path: Path):
    nav = '''<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <body><nav epub:type="toc"><a href="text/missing.xhtml">Missing</a></nav></body>
</html>'''
    opf = _opf(
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        "",
    )
    path = _write_epub(
        tmp_path,
        container=CONTAINER,
        opf=opf,
        files={"EPUB/nav.xhtml": nav},
    )
    errors = validate_epub(path)
    assert any("nav target missing" in error for error in errors)


def test_container_must_resolve_to_existing_opf(tmp_path: Path):
    container = CONTAINER.replace("EPUB/content.opf", "EPUB/missing.opf")
    path = _write_epub(
        tmp_path,
        container=container,
        opf="<package xmlns=\"http://www.idpf.org/2007/opf\" version=\"3.0\" />",
    )
    errors = validate_epub(path)
    assert any("container rootfile missing" in error for error in errors)

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from novel_epub.models import Book, Chapter, Paragraph, ParagraphBoundary, Volume
from novel_epub.renderers.native import NativeRenderer


def make_book() -> Book:
    return Book(
        title="測試書",
        author="作者",
        language="zh-TW",
        preamble=[Paragraph("前言第一段"), Paragraph("前言第二段")],
        volumes=[
            Volume(
                sequence=1,
                number="1",
                label="第一卷",
                title="九洲一号群",
                chapters=[
                    Chapter(
                        sequence=1,
                        number="1",
                        label="第1章",
                        title="開始",
                        paragraphs=[
                            Paragraph("普通段落"),
                            Paragraph("展開段落", ParagraphBoundary.EXPANDED),
                            Paragraph("場景切換", ParagraphBoundary.SCENE_BREAK),
                            Paragraph('literal <tag> & "text"\n第二行'),
                        ],
                    )
                ],
            )
        ],
    )


def test_native_renderer_emits_minimal_xhtml_and_reuses_package_builder(tmp_path: Path):
    output = tmp_path / "book.epub"

    NativeRenderer().render(make_book(), output)

    with zipfile.ZipFile(output) as zf:
        chapter = ET.fromstring(zf.read("EPUB/text/ch000001.xhtml"))
        ns = {"x": "http://www.w3.org/1999/xhtml"}
        assert chapter.find("./x:head/x:title", ns).text == "第1章 開始"
        assert chapter.find("./x:body/x:h1", ns).text == "第1章 開始"
        stylesheet = chapter.find("./x:head/x:link[@rel='stylesheet']", ns)
        assert stylesheet.attrib["href"] == "../styles/stylesheet.css"

        paragraphs = chapter.findall(".//x:body/x:p", ns)
        assert [p.attrib.get("class") for p in paragraphs] == [
            None,
            "paragraph-expanded",
            "paragraph-scene-break",
            None,
        ]
        assert paragraphs[0].text == "普通段落"
        assert paragraphs[3].text == 'literal <tag> & "text"'
        assert paragraphs[3][0].tail == "\n第二行"

        assert "EPUB/text/preamble.xhtml" in zf.namelist()
        assert "EPUB/content.opf" in zf.namelist()
        assert "EPUB/nav.xhtml" in zf.namelist()


def test_native_renderer_renders_preamble_xhtml_content(tmp_path: Path):
    output = tmp_path / "book.epub"

    NativeRenderer().render(make_book(), output)

    with zipfile.ZipFile(output) as zf:
        preamble = ET.fromstring(zf.read("EPUB/text/preamble.xhtml"))
        ns = {"x": "http://www.w3.org/1999/xhtml"}
        assert preamble.find("./x:head/x:title", ns).text == "測試書"
        assert preamble.find("./x:body/x:h1", ns).text == "測試書"
        paragraphs = preamble.findall(".//x:body/x:p", ns)
        assert [p.text for p in paragraphs] == ["前言第一段", "前言第二段"]
        assert "\\n" not in zf.read("EPUB/text/preamble.xhtml").decode("utf-8")



def test_native_renderer_preserves_navigation_and_metadata(tmp_path: Path):
    output = tmp_path / "book.epub"

    NativeRenderer().render(make_book(), output)

    with zipfile.ZipFile(output) as zf:
        opf = ET.fromstring(zf.read("EPUB/content.opf"))
        opf_ns = {
            "opf": "http://www.idpf.org/2007/opf",
            "dc": "http://purl.org/dc/elements/1.1/",
        }
        assert opf.attrib["version"] == "3.0"
        assert opf.find("opf:metadata/dc:title", opf_ns).text == "測試書"
        assert opf.find("opf:metadata/dc:creator", opf_ns).text == "作者"
        assert opf.find("opf:metadata/dc:language", opf_ns).text == "zh-TW"

        spine = [
            item.attrib["idref"]
            for item in opf.findall("opf:spine/opf:itemref", opf_ns)
        ]
        assert spine == ["preamble", "ch000001"]

        nav = zf.read("EPUB/nav.xhtml").decode("utf-8")
        assert "前言" in nav
        assert "第一卷 九洲一号群" in nav
        assert "第1章 開始" in nav


def test_native_renderer_preserves_chapter_order_across_volumes(tmp_path: Path):
    book = make_book()
    book.volumes[0].chapters.append(
        Chapter(
            sequence=2,
            number="2",
            label="第2章",
            title="第二章",
            paragraphs=[Paragraph("第二章內容")],
        )
    )
    book.volumes.append(
        Volume(
            sequence=2,
            number="2",
            label="第二卷",
            title="後續",
            chapters=[
                Chapter(
                    sequence=3,
                    number="3",
                    label="第3章",
                    title="第三章",
                    paragraphs=[Paragraph("第三章內容")],
                )
            ],
        )
    )
    output = tmp_path / "book.epub"

    NativeRenderer().render(book, output)

    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
        assert names[names.index("EPUB/text/ch000001.xhtml"):] [:3] == [
            "EPUB/text/ch000001.xhtml",
            "EPUB/text/ch000002.xhtml",
            "EPUB/text/ch000003.xhtml",
        ]
        opf = ET.fromstring(zf.read("EPUB/content.opf"))
        opf_ns = {"opf": "http://www.idpf.org/2007/opf"}
        spine = [
            item.attrib["idref"]
            for item in opf.findall("opf:spine/opf:itemref", opf_ns)
        ]
        assert spine == ["preamble", "ch000001", "ch000002", "ch000003"]


def test_native_renderer_rejects_duplicate_chapter_sequences(tmp_path: Path):
    book = make_book()
    book.volumes.append(
        Volume(
            sequence=2,
            number="2",
            label="第二卷",
            title="後續",
            chapters=[
                Chapter(
                    sequence=1,
                    number="2",
                    label="第2章",
                    title="重複",
                    paragraphs=[Paragraph("內容")],
                )
            ],
        )
    )

    try:
        NativeRenderer().render(book, tmp_path / "book.epub")
    except Exception as exc:
        assert str(exc) == "duplicate chapter sequence"
    else:
        raise AssertionError("duplicate chapter sequence should fail")

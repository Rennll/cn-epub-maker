from novel_epub.analysis import analyze_document
from novel_epub.dfm import build_formatting_model
from novel_epub.parser import parse_document
from novel_epub.physical import build_physical_document


def test_parser_consumes_the_same_physical_document_and_dfm():
    document = build_physical_document([
        "　第一章 測試",
        "第一段",
        "",
        "　第二段",
    ])
    analysis = analyze_document(document)
    dfm = build_formatting_model(document, analysis)

    result = parse_document(
        document,
        title="測試",
        author="作者",
        analysis=analysis,
        formatting_model=dfm,
    )

    assert result.analysis is analysis
    assert result.formatting_model is dfm
    assert dfm.physical_document is document
    assert result.book.chapters[0].label == "第一章"
    assert result.book.chapters[0].paragraphs[0].text == "第一段"
    assert result.book.chapters[0].paragraphs[1].text == "第二段"

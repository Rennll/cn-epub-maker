import pytest

from novel_epub.analysis import analyze_document
from novel_epub.physical import build_physical_document


def test_dfm_is_a_distinct_model_built_from_shared_physical_document():
    from novel_epub.dfm import DocumentFormattingModel, build_formatting_model

    document = build_physical_document(["第一行", "", "　第二行"])
    analysis = analyze_document(document)
    dfm = build_formatting_model(document, analysis)

    assert isinstance(dfm, DocumentFormattingModel)
    assert dfm.physical_document is document
    assert dfm.analysis is analysis


def test_dfm_exposes_formatting_evidence_without_semantic_structure():
    from novel_epub.dfm import build_formatting_model

    document = build_physical_document(["第一行", "", "　第二行", "\t第三行"])
    analysis = analyze_document(document)
    dfm = build_formatting_model(document, analysis)

    assert dfm.blocks == analysis.blocks
    assert dfm.blank_line_runs == analysis.blank_line_runs
    assert dfm.patterns == analysis.patterns
    assert dfm.transitions == analysis.transitions
    assert not hasattr(dfm, "chapters")
    assert not hasattr(dfm, "paragraphs")
    assert not hasattr(dfm, "scene_breaks")


def test_dfm_rejects_analysis_from_a_different_physical_document():
    from novel_epub.dfm import build_formatting_model

    document = build_physical_document(["A"])
    other_document = build_physical_document(["B"])

    with pytest.raises(ValueError, match="same PhysicalDocument"):
        build_formatting_model(document, analyze_document(other_document))

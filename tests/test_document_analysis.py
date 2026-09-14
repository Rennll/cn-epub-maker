from novel_epub.analysis import analyze_document
from novel_epub.physical import build_physical_document


def test_physical_document_preserves_blocks_blank_runs_and_indentation():
    document = build_physical_document([
        "　　第一行",
        "第二行",
        "",
        "\t第三行",
        " \u3000第四行",
        "",
        "",
    ])
    assert [line.text for line in document.lines] == [
        "　　第一行", "第二行", "", "\t第三行", " \u3000第四行", "", ""
    ]
    assert [block.line_numbers for block in document.blocks] == [(1, 2), (4, 5)]
    assert [(run.length, run.preceding_block, run.following_block) for run in document.blank_runs] == [
        (1, 0, 1), (2, 1, None)
    ]
    assert [line.leading_pattern for line in document.lines if not line.blank] == [
        "IDEOGRAPHIC_SPACE_x2", "NO_INDENT", "TAB_x1", "MIXED"
    ]


def test_analysis_counts_patterns_and_transitions_without_semantic_labels():
    document = build_physical_document(["第一行", "　第二行", "　第三行", "", "第四行"])
    analysis = analyze_document(document)
    assert analysis.metadata.physical_line_count == 5
    assert analysis.metadata.nonblank_line_count == 4
    assert analysis.metadata.blank_line_count == 1
    assert analysis.blocks[0].line_count == 3
    assert analysis.blocks[0].first_format == "NO_INDENT"
    assert analysis.blocks[0].last_format == "IDEOGRAPHIC_SPACE_x1"
    assert {(x.from_pattern, x.to_pattern, x.count) for x in analysis.transitions} == {
        ("NO_INDENT", "IDEOGRAPHIC_SPACE_x1", 1),
        ("IDEOGRAPHIC_SPACE_x1", "IDEOGRAPHIC_SPACE_x1", 1),
    }
    assert not hasattr(analysis, "chapters")
    assert not hasattr(analysis, "paragraphs")


def test_analysis_preserves_ascii_patterns_and_does_not_cross_blank_runs():
    document = build_physical_document([
        " A",
        "  B",
        "",
        "  C",
        "  D",
    ])
    analysis = analyze_document(document)

    assert [line.leading_pattern for line in document.lines if not line.blank] == [
        "ASCII_SPACE_x1",
        "ASCII_SPACE_x2",
        "ASCII_SPACE_x2",
        "ASCII_SPACE_x2",
    ]
    assert {(x.from_pattern, x.to_pattern, x.count) for x in analysis.transitions} == {
        ("ASCII_SPACE_x1", "ASCII_SPACE_x2", 1),
        ("ASCII_SPACE_x2", "ASCII_SPACE_x2", 1),
    }
    assert analysis.blank_line_runs[0].length == 1
    assert analysis.blank_line_runs[0].preceding_block == 0
    assert analysis.blank_line_runs[0].following_block == 1


def test_analysis_is_deterministic():
    lines = ["A", "", "\tB", "C", "", "", "D"]
    assert analyze_document(build_physical_document(lines)) == analyze_document(build_physical_document(lines))

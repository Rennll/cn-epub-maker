import pytest

from novel_epub.transforms import (
    JunkCleaner,
    JunkRule,
    TransformPipeline,
    TransformationError,
    TransformResult,
)


def test_line_exact_removes_whole_line_and_canonicalizes_blank_whitespace():
    result = JunkCleaner([JunkRule("line", "exact", "ADVERTISEMENT")]).transform(
        "第一段\nADVERTISEMENT\n  \t\n第二段"
    )
    assert result.text == "第一段\n\n第二段"
    assert result.changed
    assert result.stats["matched"] == 1


def test_contains_removes_whole_target_not_substring():
    result = JunkCleaner([JunkRule("line", "contains", "廣告")]).transform(
        "保留廣告內容\n正常"
    )
    assert result.text == "正常"
    assert result.stats["removed"] == 1


def test_block_exact_preserves_boundary_blank_lines():
    result = JunkCleaner([JunkRule("block", "exact", "A\nB")]).transform(
        "A\nB\n\nC\nD"
    )
    assert result.text == "\nC\nD"


def test_invalid_regex_is_warning_and_later_rule_runs():
    result = JunkCleaner([
        JunkRule("line", "regex", "["),
        JunkRule("line", "exact", "REMOVE"),
    ]).transform("REMOVE\nKEEP")
    assert result.text == "KEEP"
    assert len(result.warnings) == 1
    assert "rule 1" in result.warnings[0]


def test_invalid_regex_warns_even_when_input_has_no_blocks():
    result = JunkCleaner([JunkRule("block", "regex", "[")]).transform("\n  \t\n")
    assert len(result.warnings) == 1
    assert "rule 1" in result.warnings[0]


def test_rules_are_sequential():
    result = JunkCleaner([
        JunkRule("line", "contains", "A"),
        JunkRule("line", "exact", "B"),
    ]).transform("A\nB\nC")
    assert result.text == "C"


def test_junk_cleaner_reports_per_rule_stats():
    result = JunkCleaner([
        JunkRule("line", "exact", "A"),
        JunkRule("line", "contains", "B"),
    ]).transform("A\nB1\nC")
    assert result.stats["rules"] == 2
    assert result.stats["per_rule"] == [
        {"rule": 1, "matched": 1, "removed": 1, "skipped": False},
        {"rule": 2, "matched": 1, "removed": 1, "skipped": False},
    ]


def test_pipeline_stops_on_transformation_error_and_does_not_run_later_transformers():
    calls: list[str] = []

    class FatalTransformer:
        name = "fatal"

        def transform(self, text: str) -> TransformResult:
            calls.append(self.name)
            raise TransformationError("output cannot be trusted")

    class LaterTransformer:
        name = "later"

        def transform(self, text: str) -> TransformResult:
            calls.append(self.name)
            return TransformResult(text + "!", True)

    with pytest.raises(TransformationError, match="fatal: output cannot be trusted"):
        TransformPipeline([FatalTransformer(), LaterTransformer()]).run("input")

    assert calls == ["fatal"]


def test_pipeline_audit_has_explicit_stage_model():
    class IdentityTransformer:
        name = "identity"

        def transform(self, text: str) -> TransformResult:
            return TransformResult(
                text=text,
                changed=False,
                warnings=["nothing to do"],
                stats={"matched": 0},
                metadata={"profile": "test"},
            )

    _, audit = TransformPipeline([IdentityTransformer()]).run("input")
    stage = audit[0]
    assert stage.name == "identity"
    assert stage.changed is False
    assert stage.warnings == ["nothing to do"]
    assert stage.stats == {"matched": 0}
    assert stage.metadata == {"profile": "test"}

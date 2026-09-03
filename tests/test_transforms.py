import pytest

from novel_epub.transforms import (
    JunkCleaner,
    JunkRule,
    OpenCCTransformer,
    PunctuationTransformer,
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
        {"rule": 1, "matched": 1, "removed": 1},
        {"rule": 2, "matched": 1, "removed": 1},
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


def test_opencc_uses_s2twp_by_default():
    result = OpenCCTransformer().transform("简体中文和后面")

    assert result.text == "簡體中文和後面"
    assert result.changed is True
    assert result.warnings == []
    assert result.metadata == {"profile": "s2twp"}


def test_opencc_s2twp_performs_actual_conversion():
    result = OpenCCTransformer(profile="s2twp").transform("电脑软件")

    assert result.text == "電腦軟體"
    assert result.changed is True


def test_opencc_can_select_a_supported_profile():
    result = OpenCCTransformer(profile="s2t").transform("简体中文")

    assert result.text == "簡體中文"
    assert result.changed is True
    assert result.metadata == {"profile": "s2t"}


def test_opencc_zero_changes_is_success():
    result = OpenCCTransformer().transform("繁體中文")

    assert result.text == "繁體中文"
    assert result.changed is False
    assert result.warnings == []
    assert result.metadata == {"profile": "s2twp"}


def test_opencc_is_idempotent():
    transformer = OpenCCTransformer()
    once = transformer.transform("简体中文和后面").text
    twice = transformer.transform(once).text

    assert twice == once


def test_opencc_invalid_profile_is_fatal():
    transformer = OpenCCTransformer(profile="does-not-exist")

    with pytest.raises(TransformationError, match="invalid OpenCC profile: does-not-exist"):
        transformer.transform("简体中文")


def test_opencc_profile_registry_boundary_is_explicit():
    assert OpenCCTransformer.available_profiles() == ("s2t", "s2twp")


def test_opencc_runtime_init_failure_is_fatal(monkeypatch):
    class BrokenOpenCC:
        def __init__(self, config):
            raise RuntimeError(f"cannot initialize {config}")

    monkeypatch.setattr("opencc.OpenCC", BrokenOpenCC)

    with pytest.raises(TransformationError, match="OpenCC conversion failed for profile 's2twp'"):
        OpenCCTransformer().transform("简體中文")


def test_opencc_runtime_conversion_failure_is_fatal(monkeypatch):
    class BrokenOpenCC:
        def __init__(self, config):
            pass

        def convert(self, text):
            raise RuntimeError("conversion failed")

    monkeypatch.setattr("opencc.OpenCC", BrokenOpenCC)

    with pytest.raises(TransformationError, match="OpenCC conversion failed for profile 's2twp'"):
        OpenCCTransformer().transform("簡體中文")


def test_pipeline_stops_when_opencc_is_fatal(monkeypatch):
    class BrokenOpenCC:
        def __init__(self, config):
            raise RuntimeError("init failed")

    class LaterTransformer:
        name = "later"

        def transform(self, text: str):
            raise AssertionError("later transformer must not run")

    monkeypatch.setattr("opencc.OpenCC", BrokenOpenCC)

    with pytest.raises(TransformationError, match="opencc: OpenCC conversion failed"):
        TransformPipeline([OpenCCTransformer(), LaterTransformer()]).run("簡體中文")


def test_punctuation_converts_direct_quote_pairs():
    result = PunctuationTransformer().transform('“你好” ‘世界’')

    assert result.text == '「你好」 『世界』'
    assert result.changed is True
    assert result.warnings == []


def test_punctuation_converts_ascii_punctuation_in_local_chinese_context():
    result = PunctuationTransformer().transform("你好,世界! 你是誰? 答案:是;好")

    assert result.text == "你好，世界！ 你是誰？ 答案：是；好"
    assert result.changed is True


def test_punctuation_preserves_english_and_non_chinese_context():
    result = PunctuationTransformer().transform("Hello, world! 123? test: yes; 中文, English, 世界!")

    assert result.text == "Hello, world! 123? test: yes; 中文， English, 世界！"


def test_punctuation_whitespace_does_not_remove_chinese_context():
    result = PunctuationTransformer().transform("中文   , 文字")

    assert result.text == "中文   ， 文字"


def test_punctuation_leading_ascii_punctuation_is_preserved():
    result = PunctuationTransformer().transform(", ! ? : ; .")

    assert result.text == ", ! ? : ; ."
    assert result.changed is False


def test_punctuation_uses_nearest_meaningful_content_for_context():
    result = PunctuationTransformer().transform("中文, English, 中文, 123, 中文?")

    assert result.text == "中文， English, 中文， 123, 中文？"


def test_punctuation_converts_chinese_sentence_period_but_not_numeric_period():
    result = PunctuationTransformer().transform("中文. 中文 1.2 中文 2.0.")

    assert result.text == "中文。 中文 1.2 中文 2.0."


def test_punctuation_ellipsis_is_processed_before_single_period():
    result = PunctuationTransformer().transform("中文... 中文.... 中文……")

    assert result.text == "中文…… 中文…… 中文……"


def test_punctuation_preserves_parentheses_brackets_braces_and_symbols():
    source = "中文() [] {} / \\ | _ = + - * % # @ < > ~"

    result = PunctuationTransformer().transform(source)

    assert result.text == source
    assert result.changed is False


def test_punctuation_protects_urls_and_email_addresses():
    source = "中文 https://example.com/a,b?x=1, test@example.com, 中文"

    result = PunctuationTransformer().transform(source)

    assert result.text == "中文 https://example.com/a,b?x=1, test@example.com， 中文"


def test_punctuation_does_not_collapse_repeated_question_or_exclamation_marks():
    result = PunctuationTransformer().transform("什麼??? 真的!!!")

    assert result.text == "什麼？？？ 真的！！！"


def test_punctuation_zero_changes_is_success():
    source = "繁體中文。 English, 123?"

    result = PunctuationTransformer().transform(source)

    assert result.text == source
    assert result.changed is False
    assert result.warnings == []


def test_punctuation_is_idempotent():
    transformer = PunctuationTransformer()
    once = transformer.transform("中文,世界... ‘你好’!").text
    twice = transformer.transform(once).text

    assert twice == once

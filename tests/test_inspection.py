import json

import pytest

from novel_epub.inspection import inspect_source


def test_inspect_accept_writes_only_accepted_rules(tmp_path):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_text("第一章\n本章字數：1234\n正文\n本章字數：5678\n", encoding="utf-8")

    rules = inspect_source(source, output, input_fn=lambda _: "a")

    assert len(rules) == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == {
        "junk_rules": [
            {
                "target": "line",
                "matcher": "regex",
                "pattern": "^本章字數：\\d+$",
            }
        ]
    }


def test_inspect_skip_does_not_write_candidate(tmp_path):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_text("正文\n本章完\n其他\n本章完\n", encoding="utf-8")

    rules = inspect_source(source, output, input_fn=lambda _: "s")

    assert rules == ()
    assert json.loads(output.read_text(encoding="utf-8")) == {"junk_rules": []}


def test_inspect_edit_revalidates_and_writes_edited_rule(tmp_path):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_text("正文\n本章完\n其他\n本章完\n", encoding="utf-8")
    answers = iter(["e", "line:contains:本章"])

    rules = inspect_source(source, output, input_fn=lambda _: next(answers))

    assert rules[0].target == "line"
    assert rules[0].matcher == "contains"
    assert rules[0].pattern == "本章"


def test_inspect_invalid_decision_allows_retry(tmp_path):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_text("正文\n本章完\n其他\n本章完\n", encoding="utf-8")
    answers = iter([" A ", "a"])

    rules = inspect_source(source, output, input_fn=lambda _: next(answers))

    assert len(rules) == 1


def test_inspect_preserves_source(tmp_path):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    original = "正文\n本章完\n其他\n本章完\n"
    source.write_text(original, encoding="utf-8")

    inspect_source(source, output, input_fn=lambda _: "s")

    assert source.read_text(encoding="utf-8") == original


def test_inspect_does_not_overwrite_existing_output(tmp_path):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_text("正文\n", encoding="utf-8")
    output.write_text('{"junk_rules": []}\n', encoding="utf-8")

    with pytest.raises(FileExistsError):
        inspect_source(source, output, input_fn=lambda _: "s")

    assert output.read_text(encoding="utf-8") == '{"junk_rules": []}\n'

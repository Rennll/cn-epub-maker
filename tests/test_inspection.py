import json

import pytest

import novel_epub.inspection as inspection
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


def test_inspect_skips_unqualified_numbered_headings(tmp_path):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_text(
        "第一章\n第1章\n正文\n第2章\n第3章\n結尾\n",
        encoding="utf-8",
    )

    def unexpected_prompt(_):
        raise AssertionError("unqualified numeric heading must not be offered for acceptance")

    rules = inspect_source(source, output, input_fn=unexpected_prompt)

    assert rules == ()
    assert json.loads(output.read_text(encoding="utf-8")) == {"junk_rules": []}


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


def test_inspect_missing_source_does_not_create_output(tmp_path):
    source = tmp_path / "missing.txt"
    output = tmp_path / "junk-config.json"

    with pytest.raises(FileNotFoundError):
        inspect_source(source, output)

    assert not output.exists()


def test_inspect_source_encoding_failure_does_not_create_output(tmp_path, monkeypatch):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_bytes("中文".encode("utf-8"))

    def fail_read_lines(_source, _encoding):
        raise UnicodeDecodeError("utf-8", b"\x80", 0, 1, "invalid start byte")

    monkeypatch.setattr(inspection, "read_lines", fail_read_lines)

    with pytest.raises(UnicodeDecodeError):
        inspect_source(source, output, encoding="ascii")

    assert not output.exists()


def test_inspect_detection_failure_does_not_create_output(tmp_path, monkeypatch):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_text("正文\n", encoding="utf-8")

    def fail_detection(_document):
        raise RuntimeError("detection failed")

    monkeypatch.setattr(inspection, "detect_document", fail_detection)

    with pytest.raises(RuntimeError, match="detection failed"):
        inspect_source(source, output)

    assert not output.exists()


def test_inspect_cancellation_does_not_create_output(tmp_path):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_text("正文\n本章完\n其他\n本章完\n", encoding="utf-8")

    def cancel(_prompt):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        inspect_source(source, output, input_fn=cancel)

    assert not output.exists()


def test_inspect_writes_output_only_after_interaction_completes(tmp_path):
    source = tmp_path / "book.txt"
    output = tmp_path / "junk-config.json"
    source.write_text("正文\n本章完\n其他\n本章完\n", encoding="utf-8")

    def accept(_prompt):
        assert not output.exists()
        return "a"

    inspect_source(source, output, input_fn=accept)

    assert output.exists()


def test_preview_broader_detects_same_count_different_locations():
    group = inspection.DetectionGroup(
        "line", "candidate", (2, 4), ("repetition",),
        inspection.JunkRule("line", "exact", "candidate"), True
    )
    preview = inspection.RulePreview(2, 2, ("candidate",), (2, 5))

    assert inspection._preview_is_broader(group, preview) is True


def test_cli_inspect_config_feeds_normal_build_pipeline(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import novel_epub.cli as cli
    import novel_epub.execution as execution

    source = tmp_path / "book.txt"
    config = tmp_path / "junk-config.json"
    epub = tmp_path / "book.epub"
    original = "第一章\n本章字數：1234\n正文內容\n本章字數：5678\n"
    source.write_text(original, encoding="utf-8")

    real_inspect_source = cli.inspect_source

    def inspect_with_answer(input_path, output_path, *, encoding=None):
        return real_inspect_source(
            input_path,
            output_path,
            encoding=encoding,
            input_fn=lambda _prompt: "a",
        )

    monkeypatch.setattr(cli, "inspect_source", inspect_with_answer)

    assert cli.main.__module__ == "novel_epub.cli"

    monkeypatch.setattr(
        cli.sys,
        "argv",
        ["novel-epub", "inspect", str(source), "--output", str(config)],
    )
    assert cli.main() == 0

    payload = json.loads(config.read_text(encoding="utf-8"))
    assert payload["junk_rules"] == [
        {
            "target": "line",
            "matcher": "regex",
            "pattern": "^本章字數：\\\\d+$",
        }
    ]

    captured = {}

    def fake_render(book, output):
        captured["book"] = book
        output = __import__("pathlib").Path(output)
        output.write_bytes(b"fake epub")
        return output

    monkeypatch.setattr(execution, "render", fake_render)
    monkeypatch.setattr(
        execution,
        "validate_epub",
        lambda _path: SimpleNamespace(ok=True, errors=[]),
    )

    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "novel-epub",
            "build",
            str(source),
            "--output",
            str(epub),
            "--title",
            "測試書",
            "--author",
            "測試作者",
            "--config",
            str(config),
        ],
    )
    assert cli.main() == 0

    rendered_text = "\\n".join(
        paragraph.text
        for volume in captured["book"].volumes
        for chapter in volume.chapters
        for paragraph in chapter.paragraphs
    )
    assert "本章字數：1234" not in rendered_text
    assert "本章字數：5678" not in rendered_text
    assert "正文內容" in rendered_text
    assert source.read_text(encoding="utf-8") == original
    assert epub.read_bytes() == b"fake epub"

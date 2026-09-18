import json

from types import SimpleNamespace

import novel_epub.cli as cli
import novel_epub.configuration_resolver as configuration_resolver
import novel_epub.execution as execution


def test_cli_inspect_config_feeds_normal_build_and_junk_cleaner(tmp_path, monkeypatch):
    source = tmp_path / "book.txt"
    config = tmp_path / "junk-config.json"
    epub = tmp_path / "book.epub"
    original = "第一章\n正文\n本章完\n其他正文\n本章完\n"

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
    monkeypatch.setitem(configuration_resolver._DEFAULTS, "renderer", "native")
    monkeypatch.setattr(
        execution,
        "validate_epub",
        lambda _path: SimpleNamespace(ok=True, errors=[]),
    )

    captured = {}

    def fake_render(_self, book, output):
        captured["paragraphs"] = [
            paragraph.text
            for volume in book.volumes
            for chapter in volume.chapters
            for paragraph in chapter.paragraphs
        ]
        output.write_bytes(b"fake epub")
        return output

    monkeypatch.setattr(execution.NativeRenderer, "render", fake_render)

    monkeypatch.setattr(
        "sys.argv",
        [
            "novel-epub",
            "inspect",
            str(source),
            "--output",
            str(config),
        ],
    )
    assert cli.main() == 0

    payload = json.loads(config.read_text(encoding="utf-8"))
    assert payload == {
        "junk_rules": [
            {
                "target": "line",
                "matcher": "exact",
                "pattern": "本章完",
            }
        ]
    }

    monkeypatch.setattr(
        "sys.argv",
        [
            "novel-epub",
            "build",
            str(source),
            "--title",
            "測試書",
            "--author",
            "測試作者",
            "--output",
            str(epub),
            "--config",
            str(config),
            "--no-opencc",
            "--no-punctuation",
        ],
    )
    assert cli.main() == 0

    assert epub.read_bytes() == b"fake epub"
    assert "本章完" not in captured["paragraphs"]
    assert "正文" in captured["paragraphs"]
    assert "其他正文" in captured["paragraphs"]
    assert source.read_text(encoding="utf-8") == original


from argparse import Namespace
from types import SimpleNamespace

from novel_epub.cli import build, main


def _build_args(tmp_path, **overrides):
    values = {
        "input": str(tmp_path / "book.txt"),
        "output": str(tmp_path / "book.epub"),
        "title": "書名",
        "author": "作者",
        "lang": "zh-CN",
        "cover": None,
        "encoding": None,
        "keep_intermediate": False,
        "intermediate": None,
        "opencc": True,
        "opencc_profile": "s2twp",
        "punctuation": True,
        "full_source": False,
    }
    values.update(overrides)
    return Namespace(**values)


def _stub_build_dependencies(monkeypatch, captured):
    monkeypatch.setattr(
        "novel_epub.cli.read_lines",
        lambda path, encoding: (["简体,中文"], "utf-8"),
    )

    def fake_parse_lines(lines, **kwargs):
        captured["lines"] = lines
        return SimpleNamespace(
            book=SimpleNamespace(
                title=kwargs["title"],
                author=kwargs["author"],
                volumes=[],
                chapter_count=0,
                paragraph_count=1,
            ),
            warnings=[],
        )

    monkeypatch.setattr("novel_epub.cli.parse_lines", fake_parse_lines)
    monkeypatch.setattr(
        "novel_epub.cli.validate_book",
        lambda book, warnings: SimpleNamespace(errors=[]),
    )
    monkeypatch.setattr("novel_epub.cli.render", lambda book, output: None)
    monkeypatch.setattr("novel_epub.cli.validate_epub", lambda output: [])


def test_build_applies_default_v2_transformations(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)

    assert build(_build_args(tmp_path)) == 0
    assert captured["lines"] == ["簡體，中文"]


def test_build_can_disable_opencc(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)

    assert build(_build_args(tmp_path, opencc=False)) == 0
    assert captured["lines"] == ["简体，中文"]


def test_build_can_disable_punctuation(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)

    assert build(_build_args(tmp_path, punctuation=False)) == 0
    assert captured["lines"] == ["簡體,中文"]


def test_build_full_source_mode_disables_content_transformations(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)

    assert build(_build_args(tmp_path, full_source=True)) == 0
    assert captured["lines"] == ["简体,中文"]


def test_main_exposes_v2_transformation_options(monkeypatch):
    captured = {}

    def fake_build(args):
        captured.update(vars(args))
        return 0

    monkeypatch.setattr("novel_epub.cli.build", fake_build)
    monkeypatch.setattr(
        "sys.argv",
        [
            "novel-epub",
            "build",
            "book.txt",
            "--title",
            "書名",
            "--author",
            "作者",
            "--opencc-profile",
            "s2t",
            "--no-punctuation",
            "--no-opencc",
            "--full-source",
        ],
    )

    assert main() == 0
    assert captured["opencc_profile"] == "s2t"
    assert captured["opencc"] is False
    assert captured["punctuation"] is False
    assert captured["full_source"] is True

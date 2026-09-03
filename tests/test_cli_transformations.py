from argparse import Namespace
from types import SimpleNamespace

from novel_epub.cli import build, main
from novel_epub.transforms import TransformAudit, TransformationError


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


def _stub_build_dependencies(monkeypatch, captured, source_lines=None):
    monkeypatch.setattr(
        "novel_epub.cli.read_lines",
        lambda path, encoding: (source_lines or ["简体,中文"], "utf-8"),
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


def test_build_preserves_newlines_and_blank_blocks_for_parser(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(
        monkeypatch,
        captured,
        source_lines=["第一行", "第二行", "", "第三行", "", "第四行"],
    )

    def fake_parse_lines(lines, **kwargs):
        from novel_epub.parser import parse_lines

        captured["lines"] = lines
        result = parse_lines(
            lines,
            title=kwargs["title"],
            author=kwargs["author"],
            language=kwargs["language"],
            cover=kwargs["cover"],
        )
        captured["paragraphs"] = [paragraph.text for paragraph in result.book.preamble]
        return result

    monkeypatch.setattr("novel_epub.cli.parse_lines", fake_parse_lines)

    assert build(_build_args(tmp_path, full_source=True)) == 0
    assert captured["lines"] == ["第一行", "第二行", "", "第三行", "", "第四行"]
    assert captured["paragraphs"] == ["第一行\n第二行", "第三行", "第四行"]


def test_build_normalizes_leading_ideographic_spaces_before_parser(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(
        monkeypatch,
        captured,
        source_lines=["　第一行", "　第二行"],
    )

    assert build(_build_args(tmp_path, full_source=True)) == 0
    assert captured["lines"] == ["第一行", "第二行"]


def test_build_reports_transformation_error_and_returns_one(tmp_path, monkeypatch, capsys):
    _stub_build_dependencies(monkeypatch, {})

    def fail_transformations(lines, args):
        raise TransformationError("OpenCC conversion failed")

    monkeypatch.setattr("novel_epub.cli._run_transformations", fail_transformations)

    assert build(_build_args(tmp_path)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "ERROR: OpenCC conversion failed" in captured.err


def test_build_full_source_mode_takes_precedence_over_transformation_options(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)

    def fail_transformer(*args, **kwargs):
        raise AssertionError("content transformations must not run in full-source mode")

    monkeypatch.setattr("novel_epub.cli.TransformPipeline", fail_transformer)

    assert (
        build(
            _build_args(
                tmp_path,
                full_source=True,
                opencc=True,
                opencc_profile="s2t",
                punctuation=True,
            )
        )
        == 0
    )
    assert captured["lines"] == ["简体,中文"]


def test_build_warning_summary_includes_transformation_warnings(tmp_path, monkeypatch, capsys):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)
    audit = [
        TransformAudit(
            name="junk_cleaner",
            changed=False,
            warnings=["rule 1 regex '[': unterminated character set; rule skipped"],
            stats={},
            metadata={},
        )
    ]
    monkeypatch.setattr("novel_epub.cli._run_transformations", lambda lines, args: (lines, audit))

    assert build(_build_args(tmp_path)) == 0
    output = capsys.readouterr()
    assert "Warnings: 1" in output.out
    assert "WARNING: junk_cleaner: rule 1 regex '[': unterminated character set; rule skipped" in output.err


def test_build_passes_transformation_audit_to_intermediate(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)
    audit = [
        TransformAudit(
            name="opencc",
            changed=True,
            warnings=[],
            stats={},
            metadata={"profile": "s2twp"},
        )
    ]

    monkeypatch.setattr("novel_epub.cli._run_transformations", lambda lines, args: (lines, audit))

    def fake_write_intermediate(book, directory, transformations=None):
        captured["transformations"] = transformations

    monkeypatch.setattr("novel_epub.cli.write_intermediate", fake_write_intermediate)

    assert build(_build_args(tmp_path, keep_intermediate=True)) == 0
    assert captured["transformations"] == audit


def test_build_runs_transformation_stages_in_documented_order(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured, source_lines=["input"])
    calls = []

    class FakeTransformer:
        def __init__(self, name):
            self.name = name

        def transform(self, text):
            calls.append((self.name, text))
            return SimpleNamespace(
                text=f"{text}|{self.name}",
                changed=True,
                warnings=[],
                stats={},
                metadata={},
            )

    monkeypatch.setattr("novel_epub.cli.JunkCleaner", lambda: FakeTransformer("junk_cleaner"))
    monkeypatch.setattr(
        "novel_epub.cli.OpenCCTransformer",
        lambda profile: FakeTransformer("opencc"),
    )
    monkeypatch.setattr("novel_epub.cli.PunctuationTransformer", lambda: FakeTransformer("punctuation"))

    assert build(_build_args(tmp_path)) == 0
    assert calls == [
        ("junk_cleaner", "input"),
        ("opencc", "input|junk_cleaner"),
        ("punctuation", "input|junk_cleaner|opencc"),
    ]
    assert captured["lines"] == ["input|junk_cleaner|opencc|punctuation"]


def test_build_writes_transformation_audit_to_intermediate_json(tmp_path, monkeypatch):
    from novel_epub.intermediate import write_intermediate
    import json

    monkeypatch.setattr("novel_epub.cli.render", lambda book, output: None)
    monkeypatch.setattr("novel_epub.cli.validate_epub", lambda output: [])
    monkeypatch.setattr("novel_epub.cli._run_transformations", lambda lines, args: (
        lines,
        [
            TransformAudit(
                name="opencc",
                changed=True,
                warnings=["test warning"],
                stats={"matched": 2},
                metadata={"profile": "s2twp"},
            )
        ],
    ))
    monkeypatch.setattr("novel_epub.cli.read_lines", lambda path, encoding: (["簡體中文"], "utf-8"))

    def fake_input_parser(lines, **kwargs):
        from novel_epub.models import Book

        return SimpleNamespace(book=Book(title=kwargs["title"], author=kwargs["author"]), warnings=[])

    monkeypatch.setattr("novel_epub.cli.parse_lines", fake_input_parser)
    monkeypatch.setattr(
        "novel_epub.cli.validate_book",
        lambda book, warnings: SimpleNamespace(errors=[]),
    )

    intermediate = tmp_path / "book.intermediate"
    args = _build_args(tmp_path, keep_intermediate=True, intermediate=str(intermediate))
    assert build(args) == 0

    metadata = json.loads((intermediate / "book.json").read_text(encoding="utf-8"))
    assert metadata["transformations"] == [
        {
            "name": "opencc",
            "changed": True,
            "warnings": ["test warning"],
            "stats": {"matched": 2},
            "metadata": {"profile": "s2twp"},
        }
    ]


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

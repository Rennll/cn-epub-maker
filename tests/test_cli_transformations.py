from types import SimpleNamespace

from novel_epub.cli import build, main
from novel_epub.cli_adapter import namespace_to_inputs
from novel_epub.configuration_resolver import resolve_conversion_request
from novel_epub.transforms import TransformAudit, TransformationError


def _build_request(tmp_path, **overrides):
    values = {
        "source": str(tmp_path / "book.txt"),
        "destination": str(tmp_path / "book.epub"),
        "title": "書名",
        "author": "作者",
        "lang": "zh-CN",
        "cover": None,
        "encoding": None,
        "opencc": True,
        "opencc_profile": "s2twp",
        "punctuation": True,
        "full_source": False,
        "paragraph_mode": None,
    }
    values.update(overrides)
    return resolve_conversion_request(values)


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
    assert build(_build_request(tmp_path)) == 0
    assert captured["lines"] == ["簡體，中文"]


def test_build_can_disable_opencc_and_punctuation(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)
    assert build(_build_request(tmp_path, opencc=False, punctuation=False)) == 0
    assert captured["lines"] == ["简体,中文"]


def test_build_full_source_disables_content_transformations(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)
    assert build(_build_request(tmp_path, full_source=True)) == 0
    assert captured["lines"] == ["简体,中文"]


def test_build_preserves_newlines_and_normalizes_before_parser(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(
        monkeypatch,
        captured,
        source_lines=["　第一行", "　第二行", "", "第三行", "", "第四行"],
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
            paragraph_mode=kwargs["paragraph_mode"],
        )
        captured["paragraphs"] = [paragraph.text for paragraph in result.book.preamble]
        return result

    monkeypatch.setattr("novel_epub.cli.parse_lines", fake_parse_lines)
    assert build(_build_request(tmp_path, full_source=True)) == 0
    assert captured["lines"] == ["第一行", "第二行", "", "第三行", "", "第四行"]
    assert captured["paragraphs"] == ["第一行\n第二行", "第三行", "第四行"]


def test_build_passes_resolved_paragraph_mode(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)
    assert build(_build_request(tmp_path, paragraph_mode="line")) == 0
    assert captured["lines"] == ["簡體，中文"]


def test_build_uses_runtime_detected_encoding_without_mutating_request(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)
    request = _build_request(tmp_path)
    original = request

    def fake_read_lines(path, encoding):
        captured["requested_encoding"] = encoding
        return (["簡體,中文"], "gb18030")

    monkeypatch.setattr("novel_epub.cli.read_lines", fake_read_lines)
    assert build(request) == 0
    assert captured["requested_encoding"] is None
    assert request == original
    assert request.policy.encoding == "auto"


def test_build_passes_only_relevant_data_to_parser(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)
    request = _build_request(tmp_path, paragraph_mode="line")

    def fake_parse_lines(lines, **kwargs):
        captured["kwargs"] = kwargs
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
    assert build(request) == 0
    assert captured["kwargs"] == {
        "title": "書名",
        "author": "作者",
        "language": "zh-CN",
        "cover": None,
        "paragraph_mode": "line",
    }


def test_build_reports_transformation_error(tmp_path, monkeypatch, capsys):
    _stub_build_dependencies(monkeypatch, {})

    def fail_transformations(lines, policy, *, full_source):
        raise TransformationError("OpenCC conversion failed")

    monkeypatch.setattr("novel_epub.cli._run_transformations", fail_transformations)
    assert build(_build_request(tmp_path)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "ERROR: OpenCC conversion failed" in captured.err


def test_build_transformation_order(tmp_path, monkeypatch):
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
    monkeypatch.setattr("novel_epub.cli.OpenCCTransformer", lambda profile: FakeTransformer("opencc"))
    monkeypatch.setattr("novel_epub.cli.PunctuationTransformer", lambda: FakeTransformer("punctuation"))

    assert build(_build_request(tmp_path)) == 0
    assert calls == [
        ("junk_cleaner", "input"),
        ("opencc", "input|junk_cleaner"),
        ("punctuation", "input|junk_cleaner|opencc"),
    ]
    assert captured["lines"] == ["input|junk_cleaner|opencc|punctuation"]


def test_build_writes_transformation_audit_to_intermediate(tmp_path, monkeypatch):
    captured = {}
    _stub_build_dependencies(monkeypatch, captured)
    audit = [
        TransformAudit(
            name="opencc",
            changed=True,
            warnings=["test warning"],
            stats={"matched": 2},
            metadata={"profile": "s2twp"},
        )
    ]
    monkeypatch.setattr(
        "novel_epub.cli._run_transformations",
        lambda lines, policy, *, full_source: (lines, audit),
    )
    monkeypatch.setattr(
        "novel_epub.cli.write_intermediate",
        lambda book, directory, transformations=None: captured.update(transformations=transformations),
    )

    request = _build_request(tmp_path)
    assert build(request, keep_intermediate=True) == 0
    assert captured["transformations"] == audit


def test_main_uses_cli_adapter_and_resolver(monkeypatch):
    captured = {}

    def fake_resolve(values):
        captured["values"] = values
        return object()

    def fake_build(request, *, keep_intermediate=False, intermediate=None):
        captured["request"] = request
        captured["keep_intermediate"] = keep_intermediate
        captured["intermediate"] = intermediate
        return 0

    monkeypatch.setattr("novel_epub.cli.resolve_conversion_request", fake_resolve)
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
            "--keep-intermediate",
            "--intermediate",
            "book.intermediate",
        ],
    )

    assert main() == 0
    assert captured["values"]["source"] == "book.txt"
    assert captured["values"]["destination"] is None
    assert captured["values"]["opencc_profile"] == "s2t"
    assert captured["values"]["opencc"] is False
    assert captured["values"]["punctuation"] is False
    assert captured["values"]["full_source"] is True
    assert captured["keep_intermediate"] is True
    assert captured["intermediate"] == "book.intermediate"


def test_namespace_adapter_keeps_cli_omissions_distinguishable():
    from argparse import Namespace

    args = Namespace(
        input="book.txt",
        output=None,
        title="書名",
        author="作者",
        lang=None,
        cover=None,
        encoding=None,
        opencc=None,
        opencc_profile=None,
        punctuation=None,
        full_source=None,
        paragraph_mode=None,
    )
    values = namespace_to_inputs(args)
    assert values["source"] == "book.txt"
    assert values["destination"] is None
    assert values["opencc"] is None
    assert values["paragraph_mode"] is None

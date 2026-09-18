from __future__ import annotations

from pathlib import Path

from novel_epub.configuration import (
    BookMetadata,
    ConversionPolicy,
    ConversionRequest,
    JunkCleanerConfig,
    OpenCCConfig,
    ParserPolicy,
    TransformationPolicy,
)
from novel_epub.execution import ExecutionResult, execute
from novel_epub.transforms import JunkRule
from novel_epub.validation.report import ValidationReport


def _request(source: Path, destination: Path) -> ConversionRequest:
    return ConversionRequest(
        source=source,
        book_metadata=BookMetadata(
            title="Test Book",
            author="Test Author",
            language="zh-CN",
            cover=None,
        ),
        destination=destination,
        policy=ConversionPolicy(
            encoding="utf-8",
            parser=ParserPolicy(paragraph_mode="wrapped"),
            transformations=TransformationPolicy(
                opencc=OpenCCConfig(enabled=False, profile="s2twp"),
                punctuation_enabled=False,
                junk_cleaner=JunkCleanerConfig(rules=()),
            ),
            full_source=True,
        ),
    )


def test_execute_returns_structured_result_without_stdout_side_effects(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "source.txt"
    destination = tmp_path / "book.epub"
    source.write_text("第1章\n\n正文\n", encoding="utf-8")

    monkeypatch.setattr(
        "novel_epub.execution.render",
        lambda book, path: Path(path).write_bytes(b"epub"),
    )
    monkeypatch.setattr("novel_epub.execution.validate_epub", lambda path: ValidationReport())

    result = execute(_request(source, destination))

    assert isinstance(result, ExecutionResult)
    assert result.return_code == 0
    assert result.encoding == "utf-8"
    assert result.book_summary == {
        "title": "Test Book",
        "author": "Test Author",
        "volumes": 0,
        "chapters": 1,
        "paragraphs": 1,
    }
    assert result.epub_path == destination
    assert result.intermediate_path is None
    assert result.validation is not None
    assert result.epub_validation_errors == []
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_execute_captures_errors_in_result_without_printing(tmp_path, capsys):
    source = tmp_path / "missing.txt"
    destination = tmp_path / "book.epub"

    result = execute(_request(source, destination))

    assert result.return_code == 1
    assert result.errors
    assert "required executable or file not found" in result.errors[0]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_execute_builds_physical_document_from_transformed_lines(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    destination = tmp_path / "book.epub"
    source.write_text("廣告\n正文\n", encoding="utf-8")
    request = ConversionRequest(
        source=source,
        book_metadata=BookMetadata(
            title="Test Book", author="Test Author", language="zh-CN", cover=None
        ),
        destination=destination,
        policy=ConversionPolicy(
            encoding="utf-8",
            parser=ParserPolicy(paragraph_mode="wrapped"),
            transformations=TransformationPolicy(
                opencc=OpenCCConfig(enabled=False, profile="s2twp"),
                punctuation_enabled=False,
                junk_cleaner=JunkCleanerConfig(
                    rules=(JunkRule(target="line", matcher="exact", pattern="廣告"),)
                ),
            ),
            full_source=False,
        ),
    )

    captured = {}

    def fake_parse_lines(lines, **kwargs):
        captured["lines"] = lines
        captured["physical_document"] = kwargs["physical_document"]
        return type("ParseResult", (), {
            "book": type("Book", (), {
                "title": kwargs["title"],
                "author": kwargs["author"],
                "volumes": [],
                "chapter_count": 0,
                "paragraph_count": 1,
            })(),
            "warnings": [],
        })()

    monkeypatch.setattr("novel_epub.execution.parse_lines", fake_parse_lines)
    monkeypatch.setattr(
        "novel_epub.execution.validate_book",
        lambda book, warnings: type("Report", (), {"errors": [], "warnings": []})(),
    )
    monkeypatch.setattr("novel_epub.execution.render", lambda book, path: None)
    monkeypatch.setattr("novel_epub.execution.validate_epub", lambda path: [])

    result = execute(request)

    assert result.return_code == 0
    assert captured["lines"] == ["正文", ""]
    assert [line.text for line in captured["physical_document"].lines] == ["正文", ""]
    assert result.audit[0].name == "junk_cleaner"
    assert result.audit[0].changed is True

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
from novel_epub.execution import execute
from novel_epub.validation.report import ValidationReport


def _auto_request(source: Path, destination: Path) -> ConversionRequest:
    return ConversionRequest(
        source=source,
        book_metadata=BookMetadata(
            title="Test Book", author="Test Author", language="zh-CN", cover=None
        ),
        destination=destination,
        destination_mode="explicit",
        policy=ConversionPolicy(
            encoding="auto",
            parser=ParserPolicy(paragraph_mode="wrapped"),
            transformations=TransformationPolicy(
                opencc=OpenCCConfig(enabled=False, profile="s2twp"),
                punctuation_enabled=False,
                junk_cleaner=JunkCleanerConfig(rules=()),
            ),
            full_source=True,
        ),
    )


def test_execute_records_auto_detected_encoding_without_mutating_request(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    destination = tmp_path / "book.epub"
    source.write_text("第一章 開始\n正文段落\n", encoding="utf-8")
    request = _auto_request(source, destination)

    monkeypatch.setattr("novel_epub.execution.render", lambda book, path: None)
    monkeypatch.setattr("novel_epub.execution.validate_epub", lambda path: ValidationReport())

    result = execute(request)

    assert result.return_code == 0
    assert result.encoding == "utf-8"
    assert request.policy.encoding == "auto"


def test_execute_stops_before_downstream_processing_when_auto_detection_fails(
    tmp_path, monkeypatch
):
    source = tmp_path / "bad.txt"
    destination = tmp_path / "book.epub"
    source.write_bytes(bytes(range(128, 160)))
    called = False

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("downstream parsing must not run after encoding detection failure")

    monkeypatch.setattr("novel_epub.execution.parse_lines", fail_if_called)

    result = execute(_auto_request(source, destination))

    assert result.return_code == 1
    assert result.encoding == ""
    assert result.errors
    assert "unable to detect encoding" in result.errors[0]
    assert called is False

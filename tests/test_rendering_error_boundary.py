from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

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
from novel_epub.renderers.pandoc import RenderingError, _run_pandoc


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
        destination_mode="explicit",
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


def test_run_pandoc_wraps_called_process_error(monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(
            2,
            args[0],
            stderr="pandoc: invalid input",
        )

    monkeypatch.setattr("novel_epub.renderers.pandoc.subprocess.run", fail)

    try:
        _run_pandoc(["pandoc", "input.md"])
    except RenderingError as exc:
        assert "exit code 2" in str(exc)
        assert "pandoc: invalid input" in str(exc)
    else:
        raise AssertionError("RenderingError was not raised")


def test_execute_captures_rendering_error_without_output_side_effects(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "source.txt"
    destination = tmp_path / "book.epub"
    source.write_text("第1章\n\n正文\n", encoding="utf-8")

    monkeypatch.setattr(
        "novel_epub.execution.validate_book",
        lambda book, warnings: SimpleNamespace(errors=[], warnings=[]),
    )
    monkeypatch.setattr(
        "novel_epub.execution.render",
        lambda book, path: (_ for _ in ()).throw(
            RenderingError("Pandoc rendering failed with exit code 2: invalid input")
        ),
    )

    result = execute(_request(source, destination))

    assert isinstance(result, ExecutionResult)
    assert result.return_code == 1
    assert result.errors == [
        "Pandoc rendering failed with exit code 2: invalid input"
    ]
    assert result.epub_path is None
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

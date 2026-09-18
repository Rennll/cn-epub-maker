from argparse import Namespace
from pathlib import Path

from novel_epub.cli import validate
from novel_epub.validator import EpubCheckResult
from novel_epub.validation.report import ValidationReport


def test_validate_runs_epubcheck_when_available(tmp_path: Path, monkeypatch, capsys):
    epub = tmp_path / "book.epub"
    epub.write_bytes(b"")

    monkeypatch.setattr("novel_epub.cli.validate_epub", lambda path: ValidationReport())
    monkeypatch.setattr(
        "novel_epub.cli.run_epubcheck",
        lambda path, required=False: EpubCheckResult(available=True, ok=True, errors=[]),
    )

    assert validate(Namespace(epub=str(epub), require_epubcheck=False)) == 0
    assert "OK:" in capsys.readouterr().out


def test_validate_does_not_fail_when_epubcheck_unavailable(tmp_path: Path, monkeypatch, capsys):
    epub = tmp_path / "book.epub"
    epub.write_bytes(b"")

    monkeypatch.setattr("novel_epub.cli.validate_epub", lambda path: ValidationReport())
    monkeypatch.setattr(
        "novel_epub.cli.run_epubcheck",
        lambda path, required=False: EpubCheckResult(available=False, ok=True, errors=[]),
    )

    assert validate(Namespace(epub=str(epub), require_epubcheck=False)) == 0
    assert "EPUBCheck executable not found" in capsys.readouterr().err


def test_validate_fails_when_epubcheck_reports_errors(tmp_path: Path, monkeypatch, capsys):
    epub = tmp_path / "book.epub"
    epub.write_bytes(b"")

    monkeypatch.setattr("novel_epub.cli.validate_epub", lambda path: ValidationReport())
    monkeypatch.setattr(
        "novel_epub.cli.run_epubcheck",
        lambda path, required=False: EpubCheckResult(
            available=True,
            ok=False,
            errors=["ERROR(RSC-005) bad.xhtml"],
        ),
    )

    assert validate(Namespace(epub=str(epub), require_epubcheck=False)) == 1
    assert "ERROR: ERROR(RSC-005) bad.xhtml" in capsys.readouterr().err


def test_validate_requires_epubcheck_when_requested(tmp_path: Path, monkeypatch, capsys):
    epub = tmp_path / "book.epub"
    epub.write_bytes(b"")

    monkeypatch.setattr("novel_epub.cli.validate_epub", lambda path: ValidationReport())
    monkeypatch.setattr(
        "novel_epub.cli.run_epubcheck",
        lambda path, required=False: EpubCheckResult(
            available=False,
            ok=False,
            errors=["EPUBCheck executable not found"],
        ),
    )

    assert validate(Namespace(epub=str(epub), require_epubcheck=True)) == 1
    assert "EPUBCheck executable not found" in capsys.readouterr().err

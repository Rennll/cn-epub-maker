from argparse import Namespace
from pathlib import Path

from novel_epub.cli import validate
from novel_epub.validator import EpubCheckResult


def test_validate_runs_epubcheck_when_available(tmp_path: Path, monkeypatch, capsys):
    epub = tmp_path / "book.epub"
    epub.write_bytes(b"")

    monkeypatch.setattr("novel_epub.cli.validate_epub", lambda path: [])
    monkeypatch.setattr(
        "novel_epub.cli.run_epubcheck",
        lambda path: EpubCheckResult(available=True, ok=True, errors=[]),
        raising=False,
    )

    assert validate(Namespace(epub=str(epub))) == 0
    assert "OK:" in capsys.readouterr().out


def test_validate_does_not_fail_when_epubcheck_unavailable(tmp_path: Path, monkeypatch, capsys):
    epub = tmp_path / "book.epub"
    epub.write_bytes(b"")

    monkeypatch.setattr("novel_epub.cli.validate_epub", lambda path: [])
    monkeypatch.setattr(
        "novel_epub.cli.run_epubcheck",
        lambda path: EpubCheckResult(available=False, ok=True, errors=[]),
        raising=False,
    )

    assert validate(Namespace(epub=str(epub))) == 0
    assert "OK:" in capsys.readouterr().out


def test_validate_fails_when_epubcheck_reports_errors(tmp_path: Path, monkeypatch, capsys):
    epub = tmp_path / "book.epub"
    epub.write_bytes(b"")

    monkeypatch.setattr("novel_epub.cli.validate_epub", lambda path: [])
    monkeypatch.setattr(
        "novel_epub.cli.run_epubcheck",
        lambda path: EpubCheckResult(
            available=True,
            ok=False,
            errors=["ERROR(RSC-005) bad.xhtml"],
        ),
        raising=False,
    )

    assert validate(Namespace(epub=str(epub))) == 1
    assert "ERROR: ERROR(RSC-005) bad.xhtml" in capsys.readouterr().err

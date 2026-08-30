from pathlib import Path
import shutil
import subprocess

import novel_epub.validator as validator


def test_epubcheck_skips_when_command_is_unavailable(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda command: None)
    monkeypatch.setattr(validator, "shutil", shutil, raising=False)
    result = validator.run_epubcheck(tmp_path / "book.epub")
    assert result.available is False
    assert result.ok is True
    assert result.errors == []


def test_epubcheck_success_is_reported(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda command: "/usr/bin/epubcheck")
    monkeypatch.setattr(subprocess, "run", lambda command, **kwargs: type("Completed", (), {
        "returncode": 0,
        "stdout": "No errors or warnings detected.",
        "stderr": "",
    })())
    monkeypatch.setattr(validator, "shutil", shutil, raising=False)
    monkeypatch.setattr(validator, "subprocess", subprocess, raising=False)
    result = validator.run_epubcheck(tmp_path / "book.epub")
    assert result.available is True
    assert result.ok is True
    assert result.errors == []


def test_epubcheck_failure_exposes_output(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda command: "/usr/bin/epubcheck")
    monkeypatch.setattr(subprocess, "run", lambda command, **kwargs: type("Completed", (), {
        "returncode": 1,
        "stdout": "ERROR(RSC-005) bad.xhtml",
        "stderr": "EPUB validation failed",
    })())
    monkeypatch.setattr(validator, "shutil", shutil, raising=False)
    monkeypatch.setattr(validator, "subprocess", subprocess, raising=False)
    result = validator.run_epubcheck(tmp_path / "book.epub")
    assert result.available is True
    assert result.ok is False
    assert "ERROR(RSC-005) bad.xhtml" in result.errors
    assert "EPUB validation failed" in result.errors

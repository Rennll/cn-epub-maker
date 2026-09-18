from pathlib import Path

from novel_epub.validator import EpubCheckResult, run_epubcheck


def test_epubcheck_unavailable_is_not_ok_when_required(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("novel_epub.validation.epubcheck.shutil.which", lambda _: None)

    result = run_epubcheck(tmp_path / "book.epub", required=True)

    assert result == EpubCheckResult(
        available=False,
        ok=False,
        errors=["EPUBCheck executable not found"],
    )


def test_epubcheck_unavailable_is_allowed_for_optional_validation(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("novel_epub.validation.epubcheck.shutil.which", lambda _: None)

    result = run_epubcheck(tmp_path / "book.epub", required=False)

    assert result == EpubCheckResult(available=False, ok=True, errors=[])


def test_epubcheck_nonzero_exit_is_validation_failure(monkeypatch, tmp_path: Path):
    class Completed:
        returncode = 1
        stdout = "ERROR: invalid EPUB"
        stderr = ""

    monkeypatch.setattr("novel_epub.validation.epubcheck.shutil.which", lambda _: "/usr/bin/epubcheck")
    monkeypatch.setattr("novel_epub.validation.epubcheck.subprocess.run", lambda *args, **kwargs: Completed())

    result = run_epubcheck(tmp_path / "book.epub", required=True)

    assert result == EpubCheckResult(
        available=True,
        ok=False,
        errors=["ERROR: invalid EPUB"],
    )

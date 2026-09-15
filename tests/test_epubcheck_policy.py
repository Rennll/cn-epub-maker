from pathlib import Path

from novel_epub.validator import EpubCheckResult, run_epubcheck


def test_epubcheck_unavailable_is_not_ok_when_required(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("novel_epub.validator.shutil.which", lambda _: None)

    result = run_epubcheck(tmp_path / "book.epub", required=True)

    assert result == EpubCheckResult(
        available=False,
        ok=False,
        errors=["EPUBCheck executable not found"],
    )


def test_epubcheck_unavailable_is_allowed_for_optional_validation(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("novel_epub.validator.shutil.which", lambda _: None)

    result = run_epubcheck(tmp_path / "book.epub", required=False)

    assert result == EpubCheckResult(available=False, ok=True, errors=[])

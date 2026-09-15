import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


FIXTURE = Path(__file__).parent / "fixtures" / "real_reader_acceptance.txt"


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_real_reader_acceptance_fixture_produces_structural_baseline(tmp_path: Path):
    output = tmp_path / "real-reader-acceptance.epub"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "novel_epub.cli",
            "build",
            str(FIXTURE),
            "--title",
            "Real Reader Acceptance Baseline",
            "--author",
            "測試作者",
            "--lang",
            "zh-TW",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert completed.returncode == 0, completed.stderr
    assert output.is_file()

    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert "mimetype" in names
        assert "META-INF/container.xml" in names
        assert "EPUB/content.opf" in names
        assert "EPUB/nav.xhtml" in names

        chapter_files = sorted(
            name for name in names if name.startswith("EPUB/text/") and name.endswith(".xhtml")
        )
        assert chapter_files
        content = "\n".join(archive.read(name).decode("utf-8") for name in chapter_files)

    assert "第一章 閱讀器驗收基線" in content
    assert "第二章 長段落與換行" in content
    assert "第三章 標點與 CJK 換行" in content
    assert "第四章 內容完整性" in content
    assert "這一段包含硬換行" in content
    assert "這一行應該仍然屬於同一個段落語意" in content
    assert "https://example.com/reader-test?a=1&amp;b=2" in content
    for punctuation in "，。！？：「」『』（）——……":
        assert punctuation in content


def test_real_reader_acceptance_fixture_encodes_parser_boundary_signals():
    lines = FIXTURE.read_text(encoding="utf-8").splitlines()

    blank_runs = []
    index = 0
    while index < len(lines):
        if lines[index] != "":
            index += 1
            continue
        start = index
        while index < len(lines) and lines[index] == "":
            index += 1
        blank_runs.append((start, index - start, index))

    assert any(run_length == 2 for _, run_length, _ in blank_runs)
    assert any(run_length >= 3 for _, run_length, _ in blank_runs)

    expanded_runs = [run for run in blank_runs if run[1] == 2]
    scene_runs = [run for run in blank_runs if run[1] >= 3]
    assert any(lines[end] == "這裡開始是一個 expanded paragraph boundary。" for _, _, end in expanded_runs)
    assert any(lines[end] == "這裡開始是一個 scene break。" for _, _, end in scene_runs)

    hard_break_index = lines.index("這一段包含硬換行")
    assert lines[hard_break_index + 1].startswith("這一行應該仍然屬於同一個段落語意")

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


FIXTURE = Path(__file__).parent / "fixtures" / "v2_e2e.txt"


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_build_real_fixture_produces_transformed_epub(tmp_path: Path):
    output = tmp_path / "v2-e2e.epub"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "novel_epub.cli",
            "build",
            str(FIXTURE),
            "--title",
            "V2 E2E 測試",
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
        chapter_files = sorted(name for name in names if name.startswith("EPUB/text/") and name.endswith(".xhtml"))
        assert chapter_files

        content = "\n".join(
            archive.read(name).decode("utf-8") for name in chapter_files
        )

    assert "这是一个测试。" not in content
    assert "這是一個測試。" in content

    dialogue = re.search(r"<p>[^<]*他說[^<]*</p>", content)
    assert dialogue is not None, repr(content)
    print(f"DEBUG dialogue XHTML: {dialogue.group(0)!r}")

    assert "他說： \"你好，世界！\"" in content
    assert "https://example.com/test?a=1,b=2" in content
    assert "test@example.com" in content
    assert "　這一行前面有全形空白。" not in content
    assert "這一行前面有全形空白。" in content
    assert "第一章 測試開始" in content
    assert "第二章 測試繼續" in content
    assert "第3章 一張丹方" in content
    assert "室友知道宋   書航" in content

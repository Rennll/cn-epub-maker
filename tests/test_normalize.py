from pathlib import Path

import pytest

from novel_epub.normalize import detect_encoding, read_lines, normalize_line


def test_normalize_removes_only_leading_ideographic_spaces():
    assert normalize_line("　　正文　保留") == "正文　保留"


def test_utf8_bom_is_detected(tmp_path: Path):
    path = tmp_path / "book.txt"
    path.write_bytes(b"\xef\xbb\xbf\xe7\xac\ac1\xe7\xab\xa0\n\xe6\xad\xa3\xe6\x96x96\x87")
    assert detect_encoding(path) == "utf-8-sig"
    lines, encoding = read_lines(path)
    assert encoding == "utf-8-sig"
    assert lines[0] == "第1章"


def test_gb18030_roundtrip(tmp_path: Path):
    path = tmp_path / "book.txt"
    text = "第1章 测试\r\n　　正文\r\n"
    path.write_bytes(text.encode("gb18030"))
    lines, encoding = read_lines(path)
    assert encoding == "gb18030"
    assert lines == ["第1章 测试", "　　正文", ""]


def test_invalid_encoding_fails_loudly(tmp_path: Path):
    path = tmp_path / "bad.txt"
    path.write_bytes(bytes(range(128, 160)))
    with pytest.raises((ValueError, UnicodeDecodeError)):
        read_lines(path)

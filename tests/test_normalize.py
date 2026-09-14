from pathlib import Path

import pytest

from novel_epub.normalize import detect_encoding, read_lines, normalize_line


def test_normalize_preserves_leading_whitespace_evidence():
    assert normalize_line("　　正文　保留") == "　　正文　保留"


def test_utf8_bom_is_detected(tmp_path: Path):
    path = tmp_path / "book.txt"
    path.write_bytes("\ufeff第1章\n正文".encode("utf-8"))
    assert detect_encoding(path) == "utf-8-sig"
    lines, encoding = read_lines(path)
    assert encoding == "utf-8-sig"
    assert lines[0] == "第1章"


def test_utf8_without_bom_is_detected(tmp_path: Path):
    path = tmp_path / "book.txt"
    path.write_text("第1章\n正文", encoding="utf-8")
    lines, encoding = read_lines(path)
    assert encoding == "utf-8"
    assert lines == ["第1章", "正文"]


def test_gb18030_roundtrip(tmp_path: Path):
    path = tmp_path / "book.txt"
    text = "第1章 测试𠀀\r\n　　正文\r\n"
    path.write_bytes(text.encode("gb18030"))
    lines, encoding = read_lines(path)
    assert encoding == "gb18030"
    assert lines == ["第1章 测试𠀀", "　　正文", ""]


def test_big5_is_supported_for_explicit_encoding(tmp_path: Path):
    path = tmp_path / "book.txt"
    text = "第1章 測試\n這是繁體中文。"
    path.write_bytes(text.encode("big5"))
    lines, encoding = read_lines(path, "big5")
    assert encoding == "big5"
    assert lines == ["第1章 測試", "這是繁體中文。"]


def test_auto_detection_uses_fixed_priority_for_ambiguous_input(tmp_path: Path):
    path = tmp_path / "book.txt"
    # GB18030 can decode this Big5 byte stream too. Auto detection deliberately
    # selects the first successful candidate rather than guessing semantically.
    path.write_bytes("第1章 測試\n這是繁體中文。".encode("big5"))
    lines, encoding = read_lines(path)
    assert encoding == "gb18030"
    assert lines != ["第1章 測試", "這是繁體中文。"]


def test_invalid_encoding_fails_loudly(tmp_path: Path):
    path = tmp_path / "bad.txt"
    path.write_bytes(bytes(range(128, 160)))
    with pytest.raises(ValueError, match="unable to detect encoding"):
        read_lines(path)


def test_explicit_encoding_does_not_fall_back_to_auto(tmp_path: Path):
    path = tmp_path / "book.txt"
    path.write_text("第1章\n正文", encoding="utf-8")
    with pytest.raises(ValueError, match="cannot decode"):
        read_lines(path, "big5")

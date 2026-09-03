from __future__ import annotations

from pathlib import Path

COMMON_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5")


def detect_encoding(path: str | Path) -> str:
    data = Path(path).read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    for encoding in COMMON_ENCODINGS[1:]:
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", data, 0, min(len(data), 1), "unable to decode TXT with supported encodings")


def read_lines(path: str | Path, encoding: str | None = None) -> tuple[list[str], str]:
    selected = encoding or detect_encoding(path)
    raw = Path(path).read_bytes()
    try:
        text = raw.decode(selected)
    except LookupError as exc:
        raise ValueError(f"unknown encoding: {selected}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"cannot decode {path} as {selected}: {exc}") from exc

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.split("\n"), selected


def normalize_line(line: str) -> str:
    # Formatting indentation in common Chinese TXT exports is represented by
    # ideographic spaces. Remove only those at the beginning; preserve content.
    return line.lstrip("\u3000")

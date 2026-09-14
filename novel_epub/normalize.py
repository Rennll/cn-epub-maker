from pathlib import Path

# Fixed runtime detection order. The order is intentionally deterministic; it is
# not a claim that every successfully decoded byte stream has been identified
# semantically or uniquely.
AUTO_ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5")


class EncodingDetectionError(ValueError):
    """Raised when auto-detection cannot decode the source with a supported encoding."""


def detect_encoding(path: str | Path) -> str:
    data = Path(path).read_bytes()
    for encoding in AUTO_ENCODING_CANDIDATES:
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    candidates = ", ".join(AUTO_ENCODING_CANDIDATES)
    raise EncodingDetectionError(
        f"unable to detect encoding for {path}; none of the supported candidates "
        f"decoded the input ({candidates})"
    )


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
    """Return a representation-normalized physical line without discarding whitespace evidence."""
    return line

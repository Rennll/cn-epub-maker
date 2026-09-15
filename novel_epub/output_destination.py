from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_UNSAFE_REPLACEMENTS = str.maketrans(
    {
        "/": "／",
        "\\": "＼",
        ":": "：",
        "*": "＊",
        "?": "？",
        '"': "＂",
        "<": "＜",
        ">": "＞",
        "|": "｜",
    }
)
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_RESERVED_RE = re.compile(
    r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:[ .]*)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class OutputDestinationPlan:
    path: Path
    warnings: list[str]


def sanitize_output_stem(value: str) -> str:
    value = _CONTROL_RE.sub("", value).translate(_UNSAFE_REPLACEMENTS)
    value = value.strip(" \t\r\n")
    value = value.strip(".")
    if not value or _RESERVED_RE.fullmatch(value):
        return ""
    return value


def _automatic_filename(title: str, author: str) -> tuple[str, bool]:
    raw = f"{title}_{author}"
    sanitized = sanitize_output_stem(raw)
    if not sanitized:
        return "book.epub", True
    return f"{sanitized}.epub", sanitized != raw


def plan_output_destination(
    *,
    source: Path,
    title: str,
    author: str,
    destination: Path | None,
) -> OutputDestinationPlan:
    if destination is not None:
        destination = Path(destination)
        if not destination.parent.is_dir():
            raise OSError(f"output parent directory does not exist: {destination.parent}")
        if destination.exists():
            raise FileExistsError(f"output destination already exists: {destination}")
        return OutputDestinationPlan(destination, [])

    parent = Path(source).parent
    if not parent.is_dir():
        raise OSError(f"output parent directory does not exist: {parent}")

    filename, changed = _automatic_filename(title, author)
    candidate = parent / filename
    warnings: list[str] = []
    if changed:
        warnings.append(f"automatic output filename sanitized: {filename}")

    if not candidate.exists():
        return OutputDestinationPlan(candidate, warnings)

    stem = candidate.stem
    suffix = candidate.suffix
    index = 1
    while True:
        candidate = parent / f"{stem} ({index:02d}){suffix}"
        if not candidate.exists():
            warnings.append(f"automatic output filename collision; selected {candidate.name}")
            return OutputDestinationPlan(candidate, warnings)
        index += 1

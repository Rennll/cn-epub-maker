from __future__ import annotations

import json
import warnings
from pathlib import Path

from .models import Book, Paragraph, ParagraphBoundary
from .transforms import TransformAudit


def paragraph_from_dict(value: dict) -> Paragraph:
    """Deserialize a paragraph with backward-compatible boundary handling."""
    text = value.get("text", "")
    raw_boundary = value.get("boundary")
    if raw_boundary is None:
        return Paragraph(text=text)
    try:
        boundary = ParagraphBoundary(raw_boundary)
    except (TypeError, ValueError):
        warnings.warn(
            f"invalid paragraph boundary {raw_boundary!r}; using normal",
            RuntimeWarning,
            stacklevel=2,
        )
        boundary = ParagraphBoundary.NORMAL
    return Paragraph(text=text, boundary=boundary)


def _paragraph_dict(paragraph: Paragraph) -> dict[str, str]:
    value: dict[str, str] = {"text": paragraph.text}
    if paragraph.boundary is not ParagraphBoundary.NORMAL:
        value["boundary"] = paragraph.boundary.value
    return value


def write_intermediate(
    book: Book,
    directory: str | Path,
    transformations: list[TransformAudit] | None = None,
) -> Path:
    root = Path(directory)
    chapters_dir = root / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    chapter_entries: list[dict] = []
    chapter_files: dict[int, str] = {}
    for index, chapter in enumerate(book.iter_chapters(), start=1):
        filename = f"{index:06d}.json"
        chapter_files[id(chapter)] = filename
        chapter_entries.append(
            {
                "sequence": chapter.sequence,
                "number": chapter.number,
                "label": chapter.label,
                "title": chapter.title,
                "file": f"chapters/{filename}",
            }
        )
        _write_json(
            chapters_dir / filename,
            {
                "sequence": chapter.sequence,
                "number": chapter.number,
                "label": chapter.label,
                "title": chapter.title,
                "paragraphs": [_paragraph_dict(p) for p in chapter.paragraphs],
            },
        )

    if book.preamble:
        _write_json(
            root / "preamble.json",
            {"paragraphs": [_paragraph_dict(p) for p in book.preamble]},
        )

    metadata = {
        "title": book.title,
        "author": book.author,
        "language": book.language,
        "cover": book.cover,
        "preamble": {"file": "preamble.json"} if book.preamble else None,
        "transformations": [
            {
                "name": stage.name,
                "changed": stage.changed,
                "warnings": stage.warnings,
                "stats": stage.stats,
                "metadata": stage.metadata,
            }
            for stage in (transformations or [])
        ],
        "volumes": [
            {
                "sequence": v.sequence,
                "number": v.number,
                "label": v.label,
                "title": v.title,
                "chapters": [
                    {
                        "sequence": c.sequence,
                        "file": f"chapters/{chapter_files[id(c)]}",
                    }
                    for c in v.chapters
                ],
            }
            for v in book.volumes
        ],
        "chapters": chapter_entries,
    }
    _write_json(root / "book.json", metadata)
    return root


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

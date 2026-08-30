from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Book, Chapter, Paragraph, Volume
from .normalize import normalize_line

DEFAULT_VOLUME_PATTERN = r"^\s*(?P<label>第\s*(?P<number>[^\s卷部冊]+)\s*(?P<unit>[卷部冊]))[\s　]*(?P<title>.*?)\s*$"
DEFAULT_CHAPTER_PATTERN = r"^\s*(?P<label>第\s*(?P<number>[^\s章集篇回]+)\s*(?P<unit>[章集篇回]))[\s　]*(?P<title>.*?)\s*$"


@dataclass
class WarningItem:
    kind: str
    line: int
    message: str


@dataclass
class ParseResult:
    book: Book
    warnings: list[WarningItem]


def _heading_match(pattern: re.Pattern[str], text: str):
    return pattern.match(text)


def parse_lines(
    lines: list[str],
    *,
    title: str,
    author: str,
    language: str = "zh-CN",
    cover: str | None = None,
    volume_pattern: str = DEFAULT_VOLUME_PATTERN,
    chapter_pattern: str = DEFAULT_CHAPTER_PATTERN,
) -> ParseResult:
    volume_re = re.compile(volume_pattern)
    chapter_re = re.compile(chapter_pattern)
    book = Book(title=title, author=author, language=language, cover=cover)
    warnings: list[WarningItem] = []
    current_volume: Volume | None = None
    current_chapter: Chapter | None = None
    chapter_sequence = 0
    volume_sequence = 0
    seen_numbers: set[str] = set()
    seen_volume_numbers: set[str] = set()
    preamble_nonempty: list[int] = []

    def add_chapter(cm, line_no: int):
        nonlocal chapter_sequence, current_chapter
        chapter_sequence += 1
        number = cm.groupdict().get("number") or ""
        label = cm.groupdict().get("label") or cm.group(0).strip()
        unit = cm.groupdict().get("unit") or "章"
        chapter_title = (cm.groupdict().get("title") or "").strip()
        if not chapter_title:
            warnings.append(WarningItem("empty_chapter", line_no, f"empty chapter: {label}"))
        if number in seen_numbers and number:
            warnings.append(WarningItem("duplicate_chapter_number", line_no, f"duplicate chapter number: {number}"))
        if number:
            seen_numbers.add(number)
        current_chapter = Chapter(
            sequence=chapter_sequence,
            number=number,
            label=label,
            title=chapter_title,
        )
        if current_volume is not None:
            current_volume.chapters.append(current_chapter)
        else:
            book.chapters.append(current_chapter)

    for line_no, raw in enumerate(lines, 1):
        line = normalize_line(raw).rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        vm = _heading_match(volume_re, stripped)
        if vm:
            volume_sequence += 1
            number = vm.groupdict().get("number") or ""
            label = vm.groupdict().get("label") or vm.group(0).strip()
            vol_title = (vm.groupdict().get("title") or "").strip()
            if number in seen_volume_numbers and number:
                warnings.append(WarningItem("duplicate_volume_number", line_no, f"duplicate volume number: {number}"))
            if number:
                seen_volume_numbers.add(number)
            current_volume = Volume(
                sequence=volume_sequence,
                number=number,
                label=label,
                title=vol_title,
            )
            book.volumes.append(current_volume)
            current_chapter = None
            continue

        cm = _heading_match(chapter_re, stripped)
        if cm:
            add_chapter(cm, line_no)
            continue

        if current_chapter is None:
            preamble_nonempty.append(line_no)
            continue

        # Preserve all non-empty body lines exactly apart from formatting
        # indentation removed by normalize_line(). Do not strip punctuation,
        # convert numerals, or silently discard suspicious content.
        current_chapter.paragraphs.append(Paragraph(text=line))

    if preamble_nonempty:
        warnings.append(
            WarningItem(
                "text_before_first_chapter",
                preamble_nonempty[0],
                f"text found before first chapter ({len(preamble_nonempty)} non-empty lines)",
            )
        )

    if not book.chapter_count:
        warnings.append(WarningItem("no_chapters", 0, "no chapters were detected"))

    return ParseResult(book=book, warnings=warnings)

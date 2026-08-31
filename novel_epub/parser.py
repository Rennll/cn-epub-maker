from __future__ import annotations

import re
from dataclasses import dataclass

from .chinese_numerals import chinese_numeral_to_int
from .models import Book, Chapter, Paragraph, Volume
from .normalize import normalize_line

DEFAULT_VOLUME_PATTERN = r"^\s*(?P<label>第\s*(?P<number>[^\s卷部冊]+)\s*(?P<unit>[卷部冊]))(?:[\s　]+(?P<title>.*?))?\s*$"
DEFAULT_CHAPTER_PATTERN = r"^\s*(?P<label>第\s*(?P<number>[^\s章集篇回]+)\s*(?P<unit>[章集篇回]))(?:[\s　]+(?P<title>.*?))?\s*$"
DEFAULT_EXTRA_PATTERN = r"^\s*(?P<label>番外(?:篇)?(?:\s*[0-9一二三四五六七八九十百千万萬零〇兩两]+)?)\s*(?:[：:]?\s*(?P<title>.*?))?\s*$"


@dataclass
class WarningItem:
    kind: str
    line: int
    message: str


@dataclass
class ParseResult:
    book: Book
    warnings: list[WarningItem]


def _parse_number(raw: str) -> int | None:
    value = raw.strip().replace(" ", "").replace("　", "")
    if not value:
        return None
    if value.isdigit():
        return int(value)
    return chinese_numeral_to_int(value)


def parse_lines(
    lines: list[str], *, title: str, author: str, language: str = "zh-CN",
    cover: str | None = None, volume_pattern: str = DEFAULT_VOLUME_PATTERN,
    chapter_pattern: str = DEFAULT_CHAPTER_PATTERN,
) -> ParseResult:
    volume_re = re.compile(volume_pattern)
    chapter_re = re.compile(chapter_pattern)
    extra_re = re.compile(DEFAULT_EXTRA_PATTERN)
    book = Book(title=title, author=author, language=language, cover=cover)
    warnings: list[WarningItem] = []
    current_volume: Volume | None = None
    current_chapter: Chapter | None = None
    chapter_sequence = 0
    volume_sequence = 0
    seen_numbers: set[int] = set()
    seen_volume_numbers: set[str] = set()
    preamble_nonempty: list[int] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if current_chapter is not None and paragraph_lines:
            current_chapter.paragraphs.append(Paragraph(text="\n".join(paragraph_lines)))
        paragraph_lines.clear()

    def add_chapter(cm, line_no: int):
        nonlocal chapter_sequence, current_chapter
        flush_paragraph()
        chapter_sequence += 1
        groups = cm.groupdict()
        raw_number = groups.get("number")
        number = _parse_number(raw_number) if raw_number else None
        label = groups.get("label") or cm.group(0).strip()
        chapter_title = (groups.get("title") or "").strip()
        if number is not None and number in seen_numbers:
            warnings.append(WarningItem("duplicate_chapter_number", line_no, f"duplicate chapter number: {number}"))
        if number is not None:
            seen_numbers.add(number)
        current_chapter = Chapter(sequence=chapter_sequence, number=number, label=label, title=chapter_title)
        if current_volume is not None:
            current_volume.chapters.append(current_chapter)
        else:
            book.chapters.append(current_chapter)

    for line_no, raw in enumerate(lines, 1):
        line = normalize_line(raw).rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue

        vm = volume_re.match(stripped)
        if vm:
            flush_paragraph()
            volume_sequence += 1
            number = vm.groupdict().get("number") or ""
            label = vm.groupdict().get("label") or vm.group(0).strip()
            vol_title = (vm.groupdict().get("title") or "").strip()
            if number in seen_volume_numbers and number:
                warnings.append(WarningItem("duplicate_volume_number", line_no, f"duplicate volume number: {number}"))
            if number:
                seen_volume_numbers.add(number)
            current_volume = Volume(sequence=volume_sequence, number=number, label=label, title=vol_title)
            book.volumes.append(current_volume)
            current_chapter = None
            continue

        cm = chapter_re.match(stripped)
        if cm:
            raw_number = cm.groupdict().get("number") or ""
            parsed = _parse_number(raw_number)
            if parsed is None:
                warnings.append(WarningItem("unparsed_chapter_number", line_no, f"could not parse chapter number: {raw_number}"))
                continue
            add_chapter(cm, line_no)
            continue

        em = extra_re.match(stripped)
        if em:
            add_chapter(em, line_no)
            continue

        if current_chapter is None:
            preamble_nonempty.append(line_no)
            continue

        paragraph_lines.append(line)
        if stripped.startswith("第") and re.search(r"[章集篇回]", stripped):
            warnings.append(WarningItem("suspicious_chapter_heading", line_no, f"possible chapter heading not matched: {stripped[:80]}"))

    flush_paragraph()
    if preamble_nonempty:
        warnings.append(WarningItem("text_before_first_chapter", preamble_nonempty[0], f"text found before first chapter ({len(preamble_nonempty)} non-empty lines)"))
    if not book.chapter_count:
        warnings.append(WarningItem("no_chapters", 0, "no chapters were detected"))
    return ParseResult(book=book, warnings=warnings)

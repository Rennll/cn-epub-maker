from __future__ import annotations

import re
from dataclasses import dataclass

from .chinese_numerals import chinese_numeral_to_int
from .models import Book, Chapter, Paragraph, ParagraphBoundary, Volume
from .normalize import normalize_line

DEFAULT_VOLUME_PATTERN = r"^\s*(?P<label>第\s*(?P<number>[^\s卷部冊]+)\s*(?P<unit>[卷部冊]))(?:[\s　]+(?P<title>.*?))?\s*$"
DEFAULT_CHAPTER_PATTERN = r"^\s*(?P<label>第\s*(?P<number>[^\s章集篇回]+)\s*(?P<unit>[章集篇回]))(?:[\s　]+(?P<title>.*?))?\s*$"
DEFAULT_EXTRA_PATTERN = r"^\s*(?P<label>番外(?:篇)?(?:\s*[0-9一二三四五六七八九十百千万萬零〇兩两]+))(?:\s*[：:]?\s*(?P<title>.*?))?\s*$"


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


def _boundary_for_blank_run(blank_count: int) -> ParagraphBoundary:
    if blank_count >= 3:
        return ParagraphBoundary.SCENE_BREAK
    if blank_count == 2:
        return ParagraphBoundary.EXPANDED
    return ParagraphBoundary.NORMAL


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
    paragraph_lines: list[str] = []
    preamble_paragraph_lines: list[str] = []
    pending_blank_count = 0

    def flush_paragraph(boundary: ParagraphBoundary | None = None) -> None:
        if current_chapter is not None and paragraph_lines:
            current_chapter.paragraphs.append(
                Paragraph(
                    text="\n".join(paragraph_lines),
                    boundary=boundary or ParagraphBoundary.NORMAL,
                )
            )
        paragraph_lines.clear()

    def flush_preamble_paragraph(boundary: ParagraphBoundary | None = None) -> None:
        if preamble_paragraph_lines:
            book.preamble.append(
                Paragraph(
                    text="\n".join(preamble_paragraph_lines),
                    boundary=boundary or ParagraphBoundary.NORMAL,
                )
            )
            preamble_paragraph_lines.clear()

    def flush_content_boundary() -> None:
        nonlocal pending_blank_count
        if current_chapter is not None:
            flush_paragraph(_boundary_for_blank_run(pending_blank_count))
        else:
            flush_preamble_paragraph(_boundary_for_blank_run(pending_blank_count))
        pending_blank_count = 0

    def add_chapter(cm, line_no: int):
        nonlocal chapter_sequence, current_chapter
        flush_content_boundary()
        flush_preamble_paragraph()
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
            pending_blank_count += 1
            continue

        if pending_blank_count:
            flush_content_boundary()

        vm = volume_re.match(stripped)
        if vm:
            flush_content_boundary()
            flush_preamble_paragraph()
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
            groups = em.groupdict()
            label = groups.get("label") or em.group(0).strip()
            chapter_title = (groups.get("title") or "").strip()
            flush_content_boundary()
            flush_preamble_paragraph()
            chapter_sequence += 1
            current_chapter = Chapter(sequence=chapter_sequence, number=None, label=label, title=chapter_title)
            if current_volume is not None:
                current_volume.chapters.append(current_chapter)
            else:
                book.chapters.append(current_chapter)
            continue

        if current_chapter is None:
            preamble_paragraph_lines.append(stripped)
            continue

        paragraph_lines.append(line)
        if stripped.startswith("第") and re.search(r"[章集篇回]", stripped):
            warnings.append(WarningItem("suspicious_chapter_heading", line_no, f"possible chapter heading not matched: {stripped[:80]}"))

    if pending_blank_count:
        flush_content_boundary()
    flush_paragraph()
    flush_preamble_paragraph()
    if not book.chapter_count:
        warnings.append(WarningItem("no_chapters", 0, "no chapters were detected"))
    return ParseResult(book=book, warnings=warnings)

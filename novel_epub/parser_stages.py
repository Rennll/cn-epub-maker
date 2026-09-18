from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from .chinese_numerals import chinese_numeral_to_int
from .models import Book, Chapter, Paragraph, ParagraphBoundary, Volume
from .normalize import normalize_line
from .physical import PhysicalDocument, PhysicalLine

DEFAULT_VOLUME_PATTERN = r"^\s*(?P<label>第\s*(?P<number>[^\s卷部冊]+)\s*(?P<unit>[卷部冊]))(?:[\s　]+(?P<title>.*?))?\s*$"
DEFAULT_CHAPTER_PATTERN = r"^\s*(?P<label>第\s*(?P<number>[^\s章集篇回]+)\s*(?P<unit>[章集篇回]))(?:[\s　]*(?P<title>.*?))?\s*$"
DEFAULT_EXTRA_PATTERN = r"^\s*(?P<label>番外(?:篇)?(?:\s*[0-9一二三四五六七八九十百千万萬零〇兩两]+))(?:\s*[：:]?\s*(?P<title>.*?))?\s*$"
ParagraphMode = Literal["wrapped", "line"]


@dataclass(frozen=True)
class WarningItem:
    kind: str
    line: int
    message: str


@dataclass(frozen=True)
class VolumeEvent:
    line: int
    number: str
    label: str
    title: str


@dataclass(frozen=True)
class ChapterEvent:
    line: int
    number: int
    label: str
    title: str


@dataclass(frozen=True)
class UnparseableChapterEvent:
    """A chapter-shaped heading whose number could not be parsed.

    Consumers must treat this event as a warning and skip it as a chapter.
    """

    line: int
    raw_number: str


@dataclass(frozen=True)
class ExtraChapterEvent:
    line: int
    label: str
    title: str


@dataclass(frozen=True)
class TextEvent:
    line: int
    text: str


@dataclass(frozen=True)
class BlankLineEvent:
    line: int


StructuralEvent = (
    VolumeEvent
    | ChapterEvent
    | UnparseableChapterEvent
    | ExtraChapterEvent
    | TextEvent
    | BlankLineEvent
)


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


class HeadingDetector:
    """Recognize configured structural headings without building semantic models."""

    def __init__(
        self,
        *,
        volume_pattern: str = DEFAULT_VOLUME_PATTERN,
        chapter_pattern: str = DEFAULT_CHAPTER_PATTERN,
        extra_pattern: str = DEFAULT_EXTRA_PATTERN,
    ) -> None:
        self.volume_re = re.compile(volume_pattern)
        self.chapter_re = re.compile(chapter_pattern)
        self.extra_re = re.compile(extra_pattern)

    def detect(self, line: PhysicalLine) -> StructuralEvent | None:
        stripped = normalize_line(line.text).rstrip().strip()

        volume_match = self.volume_re.match(stripped)
        if volume_match:
            groups = volume_match.groupdict()
            return VolumeEvent(
                line.number,
                groups.get("number") or "",
                groups.get("label") or volume_match.group(0).strip(),
                (groups.get("title") or "").strip(),
            )

        chapter_match = self.chapter_re.match(stripped)
        if chapter_match:
            groups = chapter_match.groupdict()
            raw_number = groups.get("number") or ""
            number = _parse_number(raw_number)
            if number is None:
                return UnparseableChapterEvent(line.number, raw_number)
            return ChapterEvent(
                line.number,
                number,
                groups.get("label") or chapter_match.group(0).strip(),
                (groups.get("title") or "").strip(),
            )

        extra_match = self.extra_re.match(stripped)
        if extra_match:
            groups = extra_match.groupdict()
            return ExtraChapterEvent(
                line.number,
                groups.get("label") or extra_match.group(0).strip(),
                (groups.get("title") or "").strip(),
            )

        return None


class StructuralEventGenerator:
    """Translate the shared PhysicalDocument into parser-owned structural events."""

    def __init__(self, heading_detector: HeadingDetector) -> None:
        self.heading_detector = heading_detector

    def generate(self, document: PhysicalDocument) -> list[StructuralEvent]:
        events: list[StructuralEvent] = []
        for line in document.lines:
            if line.blank:
                events.append(BlankLineEvent(line.number))
                continue

            heading = self.heading_detector.detect(line)
            if heading is not None:
                events.append(heading)
                continue

            events.append(TextEvent(line.number, normalize_line(line.text).rstrip().strip()))
        return events


class BookBuilder:
    """Consume structural events and construct the canonical Book model."""

    def __init__(
        self,
        *,
        title: str,
        author: str,
        language: str = "zh-TW",
        cover: str | None = None,
        paragraph_mode: ParagraphMode = "wrapped",
    ) -> None:
        if paragraph_mode not in {"wrapped", "line"}:
            raise ValueError(f"unsupported paragraph mode: {paragraph_mode}")
        self.book = Book(title=title, author=author, language=language, cover=cover)
        self.paragraph_mode = paragraph_mode
        self.warnings: list[WarningItem] = []
        self.current_volume: Volume | None = None
        self.current_chapter: Chapter | None = None
        self.chapter_sequence = 0
        self.volume_sequence = 0
        self.seen_numbers: set[int] = set()
        self.seen_volume_numbers: set[str] = set()
        self.paragraph_lines: list[str] = []
        self.preamble_paragraph_lines: list[str] = []
        self.pending_blank_count = 0
        self.paragraph_boundary = ParagraphBoundary.NORMAL
        self.preamble_boundary = ParagraphBoundary.NORMAL

    def _flush_paragraph(self) -> None:
        if self.current_chapter is not None and self.paragraph_lines:
            self.current_chapter.paragraphs.append(
                Paragraph(text="\n".join(self.paragraph_lines), boundary=self.paragraph_boundary)
            )
        self.paragraph_lines.clear()
        self.paragraph_boundary = ParagraphBoundary.NORMAL

    def _flush_preamble_paragraph(self) -> None:
        if self.preamble_paragraph_lines:
            self.book.preamble.append(
                Paragraph(text="\n".join(self.preamble_paragraph_lines), boundary=self.preamble_boundary)
            )
            self.preamble_paragraph_lines.clear()
        self.preamble_boundary = ParagraphBoundary.NORMAL

    def _flush_current(self) -> None:
        if self.current_chapter is not None:
            self._flush_paragraph()
        else:
            self._flush_preamble_paragraph()

    def _consume_pending_boundary(self) -> None:
        if not self.pending_blank_count:
            return
        if self.current_chapter is not None and self.current_chapter.paragraphs:
            self.paragraph_boundary = _boundary_for_blank_run(self.pending_blank_count)
        elif self.book.preamble:
            self.preamble_boundary = _boundary_for_blank_run(self.pending_blank_count)
        self.pending_blank_count = 0

    def _reset_content_boundary(self) -> None:
        self.pending_blank_count = 0
        self.paragraph_boundary = ParagraphBoundary.NORMAL
        self.preamble_boundary = ParagraphBoundary.NORMAL

    def _add_chapter(self, event: ChapterEvent) -> None:
        self._flush_current()
        self._reset_content_boundary()
        self.chapter_sequence += 1
        if event.number in self.seen_numbers:
            self.warnings.append(
                WarningItem(
                    "duplicate_chapter_number",
                    event.line,
                    f"duplicate chapter number: {event.number}",
                )
            )
        self.seen_numbers.add(event.number)
        chapter = Chapter(
            sequence=self.chapter_sequence,
            number=event.number,
            label=event.label,
            title=event.title,
        )
        self.current_chapter = chapter
        if self.current_volume is not None:
            self.current_volume.chapters.append(chapter)
        else:
            self.book.chapters.append(chapter)

    def _add_volume(self, event: VolumeEvent) -> None:
        self._flush_current()
        self._reset_content_boundary()
        self.volume_sequence += 1
        if event.number in self.seen_volume_numbers and event.number:
            self.warnings.append(
                WarningItem(
                    "duplicate_volume_number",
                    event.line,
                    f"duplicate volume number: {event.number}",
                )
            )
        if event.number:
            self.seen_volume_numbers.add(event.number)
        self.current_volume = Volume(
            sequence=self.volume_sequence,
            number=event.number,
            label=event.label,
            title=event.title,
        )
        self.book.volumes.append(self.current_volume)
        self.current_chapter = None

    def _add_extra_chapter(self, event: ExtraChapterEvent) -> None:
        self._flush_current()
        self._reset_content_boundary()
        self.chapter_sequence += 1
        chapter = Chapter(
            sequence=self.chapter_sequence,
            number=None,
            label=event.label,
            title=event.title,
        )
        self.current_chapter = chapter
        if self.current_volume is not None:
            self.current_volume.chapters.append(chapter)
        else:
            self.book.chapters.append(chapter)

    def _add_text(self, event: TextEvent) -> None:
        if self.pending_blank_count:
            self._consume_pending_boundary()
        if self.current_chapter is None:
            self.preamble_paragraph_lines.append(event.text)
            if self.paragraph_mode == "line":
                self._flush_preamble_paragraph()
            return

        self.paragraph_lines.append(event.text)
        if event.text.startswith("第") and re.search(r"[章集篇回]", event.text):
            self.warnings.append(
                WarningItem(
                    "suspicious_chapter_heading",
                    event.line,
                    f"possible chapter heading not matched: {event.text[:80]}",
                )
            )
        if self.paragraph_mode == "line":
            self._flush_paragraph()

    def consume(self, event: StructuralEvent) -> None:
        if isinstance(event, BlankLineEvent):
            self._flush_current()
            self.pending_blank_count += 1
        elif isinstance(event, VolumeEvent):
            self._add_volume(event)
        elif isinstance(event, ChapterEvent):
            self._add_chapter(event)
        elif isinstance(event, UnparseableChapterEvent):
            self.warnings.append(
                WarningItem(
                    "unparsed_chapter_number",
                    event.line,
                    f"could not parse chapter number: {event.raw_number}",
                )
            )
        elif isinstance(event, ExtraChapterEvent):
            self._add_extra_chapter(event)
        else:
            self._add_text(event)

    def build(self, events: list[StructuralEvent]) -> tuple[Book, list[WarningItem]]:
        for event in events:
            self.consume(event)
        self._flush_current()
        if not self.book.chapter_count:
            self.warnings.append(WarningItem("no_chapters", 0, "no chapters were detected"))
        return self.book, self.warnings

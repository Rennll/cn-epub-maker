from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Paragraph:
    text: str


@dataclass
class Chapter:
    sequence: int
    number: int | None
    label: str
    title: str
    paragraphs: list[Paragraph] = field(default_factory=list)


@dataclass
class Volume:
    sequence: int
    number: str
    label: str
    title: str
    chapters: list[Chapter] = field(default_factory=list)


@dataclass
class Book:
    title: str
    author: str
    language: str = "zh-CN"
    cover: str | None = None
    volumes: list[Volume] = field(default_factory=list)
    chapters: list[Chapter] = field(default_factory=list)

    def iter_chapters(self):
        for volume in self.volumes:
            yield from volume.chapters
        yield from self.chapters

    @property
    def chapter_count(self) -> int:
        return sum(1 for _ in self.iter_chapters())

    @property
    def paragraph_count(self) -> int:
        return sum(len(ch.paragraphs) for ch in self.iter_chapters())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

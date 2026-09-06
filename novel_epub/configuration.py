from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .transforms import JunkRule


@dataclass(frozen=True)
class BookMetadata:
    title: str
    author: str
    language: str = "zh-CN"
    cover: str | None = None


@dataclass(frozen=True)
class ParserPolicy:
    paragraph_mode: str = "wrapped"


@dataclass(frozen=True)
class OpenCCConfig:
    enabled: bool = True
    profile: str = "s2twp"


@dataclass(frozen=True)
class JunkCleanerConfig:
    rules: tuple[JunkRule, ...] = ()


@dataclass(frozen=True)
class TransformationPolicy:
    opencc: OpenCCConfig = field(default_factory=OpenCCConfig)
    punctuation_enabled: bool = True
    junk_cleaner: JunkCleanerConfig = field(default_factory=JunkCleanerConfig)


@dataclass(frozen=True)
class ConversionPolicy:
    encoding: str = "auto"
    parser: ParserPolicy = field(default_factory=ParserPolicy)
    transformations: TransformationPolicy = field(default_factory=TransformationPolicy)
    full_source: bool = False


@dataclass(frozen=True)
class ConversionRequest:
    source: Path
    book_metadata: BookMetadata
    destination: Path | None = None
    policy: ConversionPolicy = field(default_factory=ConversionPolicy)

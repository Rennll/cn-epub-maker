from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .transforms import JunkRule


@dataclass(frozen=True)
class BookMetadata:
    title: str
    author: str
    language: str
    cover: str | None


@dataclass(frozen=True)
class ParserPolicy:
    paragraph_mode: str


@dataclass(frozen=True)
class OpenCCConfig:
    enabled: bool
    profile: str


@dataclass(frozen=True)
class JunkCleanerConfig:
    rules: tuple[JunkRule, ...]


@dataclass(frozen=True)
class TransformationPolicy:
    opencc: OpenCCConfig
    punctuation_enabled: bool
    junk_cleaner: JunkCleanerConfig


@dataclass(frozen=True)
class ConversionPolicy:
    encoding: str
    parser: ParserPolicy
    transformations: TransformationPolicy
    full_source: bool


@dataclass(frozen=True)
class ConversionRequest:
    source: Path
    book_metadata: BookMetadata
    destination: Path
    policy: ConversionPolicy

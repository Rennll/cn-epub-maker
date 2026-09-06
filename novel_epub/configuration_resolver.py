from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .configuration import (
    BookMetadata,
    ConversionPolicy,
    ConversionRequest,
    JunkCleanerConfig,
    OpenCCConfig,
    ParserPolicy,
    TransformationPolicy,
)

_DEFAULTS: dict[str, Any] = {
    "lang": "zh-CN",
    "encoding": "auto",
    "paragraph_mode": "wrapped",
    "opencc": True,
    "opencc_profile": "s2twp",
    "punctuation": True,
    "full_source": False,
}


def resolve_conversion_request(
    values: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None = None,
    cli: Mapping[str, Any] | None = None,
) -> ConversionRequest:
    """Resolve user-facing inputs into a complete, CLI-independent request.

    Precedence is explicit CLI value > explicit config value > application default.
    ``values`` supplies the base request data and may also contain optional values.
    ``None`` means unspecified so adapters can preserve argparse's omission state.
    """
    resolved: dict[str, Any] = dict(_DEFAULTS)
    resolved.update(_specified(values))
    resolved.update(_specified(config or {}))
    resolved.update(_specified(cli or {}))

    source = Path(_require(resolved, "source"))
    title = _require(resolved, "title")
    author = _require(resolved, "author")

    encoding = resolved["encoding"]
    if not isinstance(encoding, str) or not encoding.strip():
        raise ValueError("encoding must be a non-empty string")
    if encoding == "detect":
        raise ValueError("encoding must be 'auto' or an explicit encoding")

    paragraph_mode = resolved["paragraph_mode"]
    if paragraph_mode not in {"wrapped", "line"}:
        raise ValueError(f"invalid paragraph_mode: {paragraph_mode}")

    for key in ("opencc", "punctuation", "full_source"):
        if not isinstance(resolved[key], bool):
            raise ValueError(f"{key} must be a boolean")

    language = resolved["lang"]
    if not isinstance(language, str) or not language.strip():
        raise ValueError("lang must be a non-empty string")

    cover = resolved.get("cover")
    if cover is not None and not isinstance(cover, (str, Path)):
        raise ValueError("cover must be a path-like string or None")

    opencc_enabled = resolved["opencc"]
    punctuation_enabled = resolved["punctuation"]
    junk_rules = tuple(resolved.get("junk_rules", ()))

    if resolved["full_source"]:
        opencc_enabled = False
        punctuation_enabled = False
        junk_rules = ()

    metadata = BookMetadata(
        title=title,
        author=author,
        language=language,
        cover=str(cover) if cover is not None else None,
    )
    transformations = TransformationPolicy(
        opencc=OpenCCConfig(
            enabled=opencc_enabled,
            profile=resolved["opencc_profile"],
        ),
        punctuation_enabled=punctuation_enabled,
        junk_cleaner=JunkCleanerConfig(rules=junk_rules),
    )
    policy = ConversionPolicy(
        encoding=encoding,
        parser=ParserPolicy(paragraph_mode=paragraph_mode),
        transformations=transformations,
        full_source=resolved["full_source"],
    )

    destination_value = resolved.get("destination")
    if destination_value is None:
        destination = source.with_name(f"{title}_{author}.epub")
    else:
        destination = Path(destination_value)

    return ConversionRequest(
        source=source,
        book_metadata=metadata,
        destination=destination,
        policy=policy,
    )


def _specified(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _require(values: Mapping[str, Any], key: str) -> Any:
    value = values.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"missing required configuration: {key}")
    return value

"""Frontend adapters for loading application configuration sources."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class ConfigurationFileError(ValueError):
    """Raised when a configuration file cannot be loaded as a JSON object."""


def load_config_file(path: str | Path) -> Mapping[str, Any]:
    """Load a JSON configuration object without resolving application semantics.

    The adapter owns file I/O and JSON syntax. Application-level defaults,
    precedence, canonicalization, and validation remain responsibilities of the
    Configuration Resolver and component configuration adapters.
    """
    config_path = Path(path)

    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationFileError(
            f"cannot read configuration file: {config_path}"
        ) from exc

    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigurationFileError(
            f"invalid JSON in configuration file: {config_path}"
        ) from exc

    if not isinstance(value, dict):
        raise ConfigurationFileError(
            f"top-level JSON value must be an object: {config_path}"
        )

    return value

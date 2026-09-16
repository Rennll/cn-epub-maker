"""Configuration-layer parsing and validation for JunkRule inputs."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .transforms import JunkRule


class JunkRuleConfigurationError(ValueError):
    """Raised when a configured junk rule is invalid."""


_VALID_TARGETS = {"line", "block"}
_VALID_MATCHERS = {"exact", "contains", "regex"}


def parse_junk_rule(value: Mapping[str, object] | str | JunkRule) -> JunkRule:
    """Parse or validate one rule into the canonical JunkRule representation."""
    if isinstance(value, JunkRule):
        target = value.target
        matcher = value.matcher
        pattern = value.pattern
    elif isinstance(value, str):
        target, matcher, pattern = _parse_shorthand(value)
    elif isinstance(value, Mapping):
        target = value.get("target")
        matcher = value.get("matcher")
        pattern = value.get("pattern")
    else:
        raise JunkRuleConfigurationError("junk rule must be a mapping, string, or JunkRule")

    if target is None:
        raise JunkRuleConfigurationError("junk rule is missing required field: target")
    if target not in _VALID_TARGETS:
        raise JunkRuleConfigurationError(f"invalid junk rule target: {target!r}")
    if matcher is None:
        raise JunkRuleConfigurationError("junk rule is missing required field: matcher")
    if matcher not in _VALID_MATCHERS:
        raise JunkRuleConfigurationError(f"invalid junk rule matcher: {matcher!r}")
    if not isinstance(pattern, str):
        raise JunkRuleConfigurationError("junk rule pattern must be a string")

    if matcher == "regex":
        try:
            re.compile(pattern)
        except re.error as exc:
            raise JunkRuleConfigurationError(
                f"invalid junk rule regex: {pattern!r}"
            ) from exc

    return JunkRule(target=target, matcher=matcher, pattern=pattern)


def parse_junk_rules(
    values: Sequence[Mapping[str, object] | str | JunkRule],
) -> tuple[JunkRule, ...]:
    """Parse or validate rules in input order into canonical immutable rules."""
    return tuple(parse_junk_rule(value) for value in values)


def _parse_shorthand(value: str) -> tuple[str, str, str]:
    parts = value.split(":", 2)
    if len(parts) != 3:
        raise JunkRuleConfigurationError(
            "junk rule shorthand must be TARGET:MATCHER:PATTERN"
        )
    return parts[0], parts[1], parts[2]

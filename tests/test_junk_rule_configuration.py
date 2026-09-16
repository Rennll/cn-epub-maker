import pytest

from novel_epub.transforms import JunkRule
from novel_epub.junk_rule_configuration import (
    JunkRuleConfigurationError,
    parse_junk_rule,
    parse_junk_rules,
)


def test_parse_structured_rule_returns_canonical_junk_rule():
    result = parse_junk_rule(
        {
            "target": "line",
            "matcher": "contains",
            "pattern": "本章廣告",
        }
    )

    assert result == JunkRule(
        target="line",
        matcher="contains",
        pattern="本章廣告",
    )


def test_parse_cli_shorthand_returns_same_canonical_rule():
    result = parse_junk_rule("line:contains:本章廣告")

    assert result == JunkRule(
        target="line",
        matcher="contains",
        pattern="本章廣告",
    )


def test_cli_shorthand_splits_only_first_two_separators():
    result = parse_junk_rule("line:regex:^https?://example.com:8080$")

    assert result == JunkRule(
        target="line",
        matcher="regex",
        pattern="^https?://example.com:8080$",
    )


@pytest.mark.parametrize("target", ["paragraph", "", None])
def test_invalid_target_is_configuration_error(target):
    with pytest.raises(JunkRuleConfigurationError):
        parse_junk_rule(
            {
                "target": target,
                "matcher": "exact",
                "pattern": "foo",
            }
        )


@pytest.mark.parametrize("matcher", ["glob", "", None])
def test_invalid_matcher_is_configuration_error(matcher):
    with pytest.raises(JunkRuleConfigurationError):
        parse_junk_rule(
            {
                "target": "line",
                "matcher": matcher,
                "pattern": "foo",
            }
        )


def test_non_string_pattern_is_configuration_error():
    with pytest.raises(JunkRuleConfigurationError):
        parse_junk_rule(
            {
                "target": "line",
                "matcher": "exact",
                "pattern": 123,
            }
        )


def test_invalid_regex_is_configuration_error():
    with pytest.raises(JunkRuleConfigurationError):
        parse_junk_rule(
            {
                "target": "line",
                "matcher": "regex",
                "pattern": "[unclosed",
            }
        )


def test_valid_regex_is_accepted():
    result = parse_junk_rule(
        {
            "target": "line",
            "matcher": "regex",
            "pattern": r"^廣告\\d+$",
        }
    )

    assert result == JunkRule(
        target="line",
        matcher="regex",
        pattern=r"^廣告\\d+$",
    )


def test_parse_junk_rules_preserves_input_order():
    result = parse_junk_rules(
        [
            {"target": "line", "matcher": "exact", "pattern": "first"},
            "block:contains:second",
            {"target": "line", "matcher": "regex", "pattern": "third"},
        ]
    )

    assert result == (
        JunkRule(target="line", matcher="exact", pattern="first"),
        JunkRule(target="block", matcher="contains", pattern="second"),
        JunkRule(target="line", matcher="regex", pattern="third"),
    )

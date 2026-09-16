from dataclasses import replace
from pathlib import Path

import pytest

from novel_epub.configuration_resolver import resolve_conversion_request
from novel_epub.transforms import JunkRule


def test_resolver_applies_application_defaults():
    request = resolve_conversion_request(
        {"source": "book.txt", "title": "書名", "author": "作者"}
    )

    assert request.source == Path("book.txt")
    assert request.destination == Path("書名_作者.epub")
    assert request.destination_mode == "automatic"
    assert request.book_metadata.title == "書名"
    assert request.book_metadata.author == "作者"
    assert request.book_metadata.language == "zh-CN"
    assert request.policy.encoding == "auto"
    assert request.policy.parser.paragraph_mode == "wrapped"
    assert request.policy.transformations.opencc.enabled is True
    assert request.policy.transformations.opencc.profile == "s2twp"
    assert request.policy.transformations.punctuation_enabled is True
    assert request.policy.transformations.junk_cleaner.rules == ()
    assert request.policy.full_source is False


def test_explicit_application_defaults_override_built_in_defaults():
    request = resolve_conversion_request(
        {"source": "book.txt", "title": "書名", "author": "作者"},
        application_defaults={"encoding": "big5", "paragraph_mode": "line"},
    )

    assert request.policy.encoding == "big5"
    assert request.policy.parser.paragraph_mode == "line"


def test_explicit_destination_overrides_derived_default():
    request = resolve_conversion_request(
        {
            "source": "book.txt",
            "title": "書名",
            "author": "作者",
            "destination": "output.epub",
        }
    )
    assert request.destination == Path("output.epub")
    assert request.destination_mode == "explicit"


def test_resolver_accepts_explicit_policy_values():
    request = resolve_conversion_request(
        {
            "source": "book.txt",
            "title": "書名",
            "author": "作者",
            "destination": "book.epub",
            "encoding": "utf-8",
            "lang": "zh-TW",
            "cover": "cover.jpg",
            "paragraph_mode": "line",
            "opencc": False,
            "opencc_profile": "s2t",
            "punctuation": False,
        }
    )

    assert request.policy.encoding == "utf-8"
    assert request.book_metadata.language == "zh-TW"
    assert request.book_metadata.cover == "cover.jpg"
    assert request.policy.parser.paragraph_mode == "line"
    assert request.policy.transformations.opencc.enabled is False
    assert request.policy.transformations.opencc.profile == "s2t"
    assert request.policy.transformations.punctuation_enabled is False


def test_resolver_uses_cli_values_over_config_values():
    request = resolve_conversion_request(
        {"source": "book.txt", "title": "書名", "author": "作者"},
        config_file={
            "encoding": "big5",
            "paragraph_mode": "line",
            "opencc": False,
            "punctuation": False,
        },
        cli={
            "encoding": "utf-8",
            "paragraph_mode": "wrapped",
            "opencc": True,
        },
    )

    assert request.policy.encoding == "utf-8"
    assert request.policy.parser.paragraph_mode == "wrapped"
    assert request.policy.transformations.opencc.enabled is True
    assert request.policy.transformations.punctuation_enabled is False


def test_unspecified_cli_values_do_not_override_config():
    request = resolve_conversion_request(
        {"source": "book.txt", "title": "書名", "author": "作者"},
        config_file={"encoding": "big5", "paragraph_mode": "line"},
        cli={"encoding": None, "paragraph_mode": None},
    )
    assert request.policy.encoding == "big5"
    assert request.policy.parser.paragraph_mode == "line"


def test_resolver_canonicalizes_junk_rules_from_base_input():
    request = resolve_conversion_request(
        {
            "source": "book.txt",
            "title": "書名",
            "author": "作者",
            "junk_rules": [
                {"target": "line", "matcher": "exact", "pattern": "first"},
                "block:contains:second",
            ],
        }
    )

    assert request.policy.transformations.junk_cleaner.rules == (
        JunkRule(target="line", matcher="exact", pattern="first"),
        JunkRule(target="block", matcher="contains", pattern="second"),
    )


def test_resolver_appends_config_and_cli_junk_rules_in_order():
    request = resolve_conversion_request(
        {"source": "book.txt", "title": "書名", "author": "作者"},
        config_file={
            "junk_rules": [
                {"target": "line", "matcher": "exact", "pattern": "config"}
            ]
        },
        cli={"junk_rules": ["block:contains:cli"]},
    )

    assert request.policy.transformations.junk_cleaner.rules == (
        JunkRule(target="line", matcher="exact", pattern="config"),
        JunkRule(target="block", matcher="contains", pattern="cli"),
    )


def test_resolver_rejects_invalid_junk_rule_before_execution():
    with pytest.raises(ValueError, match="junk rule"):
        resolve_conversion_request(
            {
                "source": "book.txt",
                "title": "書名",
                "author": "作者",
                "junk_rules": ["line:regex:[unclosed"],
            }
        )


def test_resolver_rejects_invalid_junk_rule_even_in_full_source_mode():
    with pytest.raises(ValueError, match="junk rule"):
        resolve_conversion_request(
            {
                "source": "book.txt",
                "title": "書名",
                "author": "作者",
                "full_source": True,
                "junk_rules": ["line:regex:[unclosed"],
            }
        )


def test_full_source_disables_effective_content_transformations():
    request = resolve_conversion_request(
        {
            "source": "book.txt",
            "title": "書名",
            "author": "作者",
            "full_source": True,
            "opencc": True,
            "punctuation": True,
            "junk_rules": ["line:exact:ignored"],
        }
    )

    assert request.policy.full_source is True
    assert request.policy.transformations.opencc.enabled is False
    assert request.policy.transformations.punctuation_enabled is False
    assert request.policy.transformations.junk_cleaner.rules == ()


def test_resolver_rejects_missing_required_fields():
    with pytest.raises(ValueError, match="source"):
        resolve_conversion_request({"title": "書名", "author": "作者"})

    with pytest.raises(ValueError, match="title"):
        resolve_conversion_request({"source": "book.txt", "author": "作者"})

    with pytest.raises(ValueError, match="author"):
        resolve_conversion_request({"source": "book.txt", "title": "書名"})


def test_resolver_rejects_invalid_application_policy_values():
    base = {"source": "book.txt", "title": "書名", "author": "作者"}

    with pytest.raises(ValueError, match="encoding"):
        resolve_conversion_request({**base, "encoding": "detect"})

    with pytest.raises(ValueError, match="paragraph_mode"):
        resolve_conversion_request({**base, "paragraph_mode": "smart"})


def test_conversion_request_rejects_invalid_destination_mode():
    request = resolve_conversion_request(
        {"source": "book.txt", "title": "書名", "author": "作者"}
    )

    with pytest.raises(ValueError, match="destination_mode"):
        replace(request, destination_mode="invalid")


def test_resolver_does_not_read_source_or_execute_transformations(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("resolver must not execute runtime work")

    monkeypatch.setattr("pathlib.Path.read_text", fail)

    request = resolve_conversion_request(
        {"source": "missing.txt", "title": "書名", "author": "作者"}
    )

    assert request.source == Path("missing.txt")

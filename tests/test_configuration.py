from pathlib import Path

import pytest

from novel_epub.configuration import (
    BookMetadata,
    ConversionPolicy,
    ConversionRequest,
    JunkCleanerConfig,
    OpenCCConfig,
    ParserPolicy,
    TransformationPolicy,
)
from novel_epub.transforms import JunkRule


def test_configuration_model_requires_resolved_values():
    with pytest.raises(TypeError):
        BookMetadata(title="書名", author="作者")
    with pytest.raises(TypeError):
        ParserPolicy()
    with pytest.raises(TypeError):
        OpenCCConfig()
    with pytest.raises(TypeError):
        ConversionPolicy()


def test_conversion_request_contains_request_data_but_not_execution_state():
    request = ConversionRequest(
        source=Path("book.txt"),
        book_metadata=BookMetadata(
            title="書名",
            author="作者",
            language="zh-TW",
            cover="cover.jpg",
        ),
        destination=Path("book.epub"),
        policy=ConversionPolicy(
            encoding="auto",
            parser=ParserPolicy(paragraph_mode="wrapped"),
            transformations=TransformationPolicy(
                opencc=OpenCCConfig(enabled=True, profile="s2twp"),
                punctuation_enabled=True,
                junk_cleaner=JunkCleanerConfig(rules=()),
            ),
            full_source=False,
        ),
    )

    assert request.source == Path("book.txt")
    assert request.destination == Path("book.epub")
    assert request.book_metadata.language == "zh-TW"
    assert request.book_metadata.cover == "cover.jpg"
    assert not hasattr(request, "book")
    assert not hasattr(request, "actual_encoding")
    assert not hasattr(request, "transformers")


def test_configuration_is_immutable():
    policy = ConversionPolicy(
        encoding="auto",
        parser=ParserPolicy(paragraph_mode="wrapped"),
        transformations=TransformationPolicy(
            opencc=OpenCCConfig(enabled=True, profile="s2twp"),
            punctuation_enabled=True,
            junk_cleaner=JunkCleanerConfig(rules=()),
        ),
        full_source=False,
    )
    request = ConversionRequest(
        source=Path("book.txt"),
        book_metadata=BookMetadata(
            title="書名", author="作者", language="zh-CN", cover=None
        ),
        destination=Path("book.epub"),
        policy=policy,
    )

    with pytest.raises(AttributeError):
        request.policy = policy

    with pytest.raises(AttributeError):
        request.policy.transformations.opencc.enabled = False


def test_junk_rules_are_stored_as_read_only_configuration_data():
    rule = JunkRule(target="line", matcher="exact", pattern="廣告")
    config = JunkCleanerConfig(rules=(rule,))

    assert config.rules == (rule,)
    with pytest.raises(AttributeError):
        config.rules += (JunkRule(target="line", matcher="exact", pattern="推廣"),)


def test_policy_types_have_single_responsibility_fields():
    parser = ParserPolicy(paragraph_mode="line")
    opencc = OpenCCConfig(enabled=False, profile="s2t")
    junk = JunkCleanerConfig(rules=())
    transformations = TransformationPolicy(
        opencc=opencc,
        punctuation_enabled=False,
        junk_cleaner=junk,
    )
    policy = ConversionPolicy(
        encoding="utf-8",
        parser=parser,
        transformations=transformations,
        full_source=True,
    )

    assert parser.paragraph_mode == "line"
    assert opencc.enabled is False
    assert opencc.profile == "s2t"
    assert transformations.punctuation_enabled is False
    assert policy.encoding == "utf-8"
    assert policy.full_source is True

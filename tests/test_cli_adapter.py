from argparse import Namespace
from pathlib import Path

from novel_epub.cli_adapter import namespace_to_inputs


def test_adapter_keeps_only_cli_configuration_fields():
    args = Namespace(
        input="book.txt",
        output="book.epub",
        title="書名",
        author="作者",
        lang="zh-TW",
        cover="cover.jpg",
        encoding=None,
        keep_intermediate=True,
        intermediate="book.intermediate",
        opencc=False,
        opencc_profile="s2t",
        punctuation=True,
        full_source=False,
        paragraph_mode="line",
    )

    values = namespace_to_inputs(args)

    assert values == {
        "source": "book.txt",
        "destination": "book.epub",
        "title": "書名",
        "author": "作者",
        "lang": "zh-TW",
        "cover": "cover.jpg",
        "encoding": None,
        "opencc": False,
        "opencc_profile": "s2t",
        "punctuation": True,
        "full_source": False,
        "paragraph_mode": "line",
    }
    assert "keep_intermediate" not in values
    assert "intermediate" not in values


def test_adapter_preserves_unspecified_cli_values_as_none():
    args = Namespace(
        input="book.txt",
        output=None,
        title="書名",
        author="作者",
        lang=None,
        cover=None,
        encoding=None,
        opencc=None,
        opencc_profile=None,
        punctuation=None,
        full_source=None,
        paragraph_mode=None,
    )

    values = namespace_to_inputs(args)

    assert values["destination"] is None
    assert values["lang"] is None
    assert values["encoding"] is None
    assert values["opencc"] is None
    assert values["opencc_profile"] is None
    assert values["punctuation"] is None
    assert values["full_source"] is None
    assert values["paragraph_mode"] is None


def test_adapter_does_not_depend_on_argparse_in_returned_data():
    args = Namespace(
        input=Path("book.txt"),
        output=Path("book.epub"),
        title="書名",
        author="作者",
        lang="zh-CN",
        cover=None,
        encoding=None,
        opencc=True,
        opencc_profile="s2twp",
        punctuation=True,
        full_source=False,
        paragraph_mode="wrapped",
    )

    values = namespace_to_inputs(args)

    assert isinstance(values, dict)
    assert all(not isinstance(value, Namespace) for value in values.values())

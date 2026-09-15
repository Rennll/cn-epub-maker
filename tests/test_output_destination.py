from pathlib import Path

import pytest

from novel_epub.output_destination import (
    plan_output_destination,
    sanitize_output_stem,
)


def test_sanitize_output_stem_replaces_unsafe_filename_characters():
    assert sanitize_output_stem(' 書/名\\作者:*?"<>|. ') == "書／名＼作者：＊？＂＜＞｜"


def test_sanitize_output_stem_removes_control_characters_and_trims_edges():
    assert sanitize_output_stem(" \t書名\n") == "書名"
    assert sanitize_output_stem("...書名...") == "書名"


def test_sanitize_output_stem_preserves_internal_whitespace():
    assert sanitize_output_stem("書名  作者") == "書名  作者"


@pytest.mark.parametrize(
    "name",
    ["CON", "con", "PRN", "AUX", "NUL", "COM1", "LPT9", "CON."],
)
def test_sanitize_output_stem_rejects_windows_reserved_device_names(name):
    assert sanitize_output_stem(name) == ""


def test_plan_automatic_destination_uses_source_parent_and_sanitizes_metadata(tmp_path):
    source = tmp_path / "source.txt"
    result = plan_output_destination(
        source=source,
        title="書/名",
        author="作者?",
        destination=None,
    )

    assert result.path == tmp_path / "書／名_作者？.epub"
    assert result.warnings
    assert any("sanit" in warning.lower() for warning in result.warnings)


def test_plan_automatic_destination_uses_collision_suffixes(tmp_path):
    source = tmp_path / "source.txt"
    (tmp_path / "書名_作者.epub").write_bytes(b"")
    (tmp_path / "書名_作者 (01).epub").write_bytes(b"")

    result = plan_output_destination(
        source=source,
        title="書名",
        author="作者",
        destination=None,
    )

    assert result.path == tmp_path / "書名_作者 (02).epub"
    assert any("collision" in warning.lower() for warning in result.warnings)


def test_plan_explicit_destination_preserves_path_without_sanitization(tmp_path):
    destination = tmp_path / "bad:name.epub"

    result = plan_output_destination(
        source=tmp_path / "source.txt",
        title="書名",
        author="作者",
        destination=destination,
    )

    assert result.path == destination
    assert result.warnings == []


def test_plan_explicit_destination_requires_existing_parent(tmp_path):
    destination = tmp_path / "missing" / "book.epub"

    with pytest.raises(OSError, match="parent"):
        plan_output_destination(
            source=tmp_path / "source.txt",
            title="書名",
            author="作者",
            destination=destination,
        )


def test_plan_explicit_destination_rejects_existing_target(tmp_path):
    destination = tmp_path / "book.epub"
    destination.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        plan_output_destination(
            source=tmp_path / "source.txt",
            title="書名",
            author="作者",
            destination=destination,
        )

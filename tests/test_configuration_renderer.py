from pathlib import Path

from novel_epub.configuration_resolver import resolve_conversion_request


def test_renderer_defaults_to_pandoc(tmp_path: Path):
    request = resolve_conversion_request(
        {
            "source": tmp_path / "input.txt",
            "title": "書",
            "author": "作者",
        }
    )

    assert request.policy.renderer == "pandoc"


def test_renderer_can_be_selected_by_configuration_layer(tmp_path: Path):
    request = resolve_conversion_request(
        {
            "source": tmp_path / "input.txt",
            "title": "書",
            "author": "作者",
        },
        config_file={"renderer": "native"},
    )

    assert request.policy.renderer == "native"


def test_invalid_renderer_is_rejected(tmp_path: Path):
    try:
        resolve_conversion_request(
            {
                "source": tmp_path / "input.txt",
                "title": "書",
                "author": "作者",
            },
            config_file={"renderer": "unknown"},
        )
    except ValueError as exc:
        assert "invalid renderer" in str(exc)
    else:
        raise AssertionError("invalid renderer should be rejected")

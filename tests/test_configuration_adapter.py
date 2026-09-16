import json

import pytest

from novel_epub.configuration_adapter import (
    ConfigurationFileError,
    load_config_file,
)


def test_load_config_file_returns_json_object_mapping(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "encoding": "utf-8",
                "junk_rules": ["line:exact:廣告"],
            }
        ),
        encoding="utf-8",
    )

    assert load_config_file(path) == {
        "encoding": "utf-8",
        "junk_rules": ["line:exact:廣告"],
    }


def test_load_config_file_accepts_path_like_string(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{}", encoding="utf-8")

    assert load_config_file(str(path)) == {}


def test_load_config_file_rejects_missing_file(tmp_path):
    with pytest.raises(ConfigurationFileError, match="cannot read configuration file"):
        load_config_file(tmp_path / "missing.json")


def test_load_config_file_rejects_invalid_json(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"encoding": ', encoding="utf-8")

    with pytest.raises(ConfigurationFileError, match="invalid JSON"):
        load_config_file(path)


def test_load_config_file_rejects_non_object_json(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ConfigurationFileError, match="top-level JSON value must be an object"):
        load_config_file(path)


def test_load_config_file_does_not_resolve_or_validate_application_values(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({"paragraph_mode": "not-an-application-value-yet"}),
        encoding="utf-8",
    )

    assert load_config_file(path) == {
        "paragraph_mode": "not-an-application-value-yet"
    }

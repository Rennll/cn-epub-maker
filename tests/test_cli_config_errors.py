import pytest

from novel_epub.cli import main
from novel_epub.configuration_adapter import ConfigurationFileError


@pytest.mark.parametrize(
    "error",
    [
        "cannot read configuration file: missing.json",
        "invalid JSON in configuration file: config.json",
        "top-level JSON value must be an object: config.json",
    ],
)
def test_main_reports_configuration_file_error_without_traceback(monkeypatch, capsys, error):
    def fake_load(path):
        raise ConfigurationFileError(error)

    monkeypatch.setattr("novel_epub.cli.load_config_file", fake_load)
    monkeypatch.setattr(
        "sys.argv",
        [
            "novel-epub",
            "build",
            "book.txt",
            "--title",
            "書名",
            "--author",
            "作者",
            "--config",
            "config.json",
        ],
    )

    assert main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"ERROR: {error}" in captured.err


def test_main_does_not_build_when_config_file_loading_fails(monkeypatch):
    monkeypatch.setattr(
        "novel_epub.cli.load_config_file",
        lambda path: (_ for _ in ()).throw(
            ConfigurationFileError("invalid JSON in configuration file: config.json")
        ),
    )

    def fail_build(*args, **kwargs):
        raise AssertionError("build must not run after configuration loading fails")

    monkeypatch.setattr("novel_epub.cli.build", fail_build)
    monkeypatch.setattr(
        "sys.argv",
        [
            "novel-epub",
            "build",
            "book.txt",
            "--title",
            "書名",
            "--author",
            "作者",
            "--config",
            "config.json",
        ],
    )

    assert main() == 1

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from novel_epub.configuration import ConversionRequest
from novel_epub.configuration_resolver import resolve_conversion_request

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "novel_epub"


def _python_files() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def test_argparse_namespace_is_restricted_to_cli_boundaries():
    allowed = {PACKAGE / "cli.py", PACKAGE / "cli_adapter.py"}

    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "argparse":
                assert path in allowed, f"argparse import leaked into {path.relative_to(ROOT)}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "argparse" or path in allowed, (
                        f"argparse import leaked into {path.relative_to(ROOT)}"
                    )


def test_application_execution_does_not_accept_argparse_namespace():
    execution = (PACKAGE / "execution.py").read_text(encoding="utf-8")
    assert "argparse" not in execution
    assert "Namespace" not in execution


def test_conversion_request_has_no_runtime_or_execution_fields():
    fields = set(ConversionRequest.__dataclass_fields__)
    forbidden = {
        "book",
        "actual_encoding",
        "detected_encoding",
        "transformers",
        "audit",
        "warnings",
        "runtime",
        "execution",
    }
    assert fields.isdisjoint(forbidden)


def test_conversion_request_cannot_be_mutated_by_runtime_assignment(tmp_path: Path):
    request = resolve_conversion_request(
        {
            "source": str(tmp_path / "book.txt"),
            "title": "書名",
            "author": "作者",
        }
    )
    original = request

    with pytest.raises(AttributeError):
        request.policy = request.policy

    assert request is original
    assert request.policy.encoding == "auto"
    assert not hasattr(request, "actual_encoding")


def test_intermediate_schema_contains_provenance_but_not_request(tmp_path: Path):
    intermediate = (PACKAGE / "intermediate.py").read_text(encoding="utf-8")
    assert "ConversionRequest" not in intermediate
    assert "TransformAudit" in intermediate
    assert "transformations" in intermediate

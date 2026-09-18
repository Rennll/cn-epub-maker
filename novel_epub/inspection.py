"""Interactive, read-only Junk Detection inspection workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .junk_detection import DetectionGroup, RulePreview, detect_document, preview_rule
from .junk_rule_configuration import JunkRuleConfigurationError, parse_junk_rule
from .normalize import read_lines
from .physical import PhysicalDocument, build_physical_document
from .transforms import JunkRule


def inspect_source(
    source: str | Path,
    output: str | Path,
    *,
    encoding: str | None = None,
    input_fn: Callable[[str], str] = input,
) -> tuple[JunkRule, ...]:
    """Inspect a source, interactively select rules, and write a new config."""
    output_path = Path(output)
    if output_path.exists():
        raise FileExistsError(f"inspection output already exists: {output_path}")

    lines, _ = read_lines(source, encoding)
    document = build_physical_document(lines)
    groups = detect_document(document)

    accepted: list[JunkRule] = []
    for index, group in enumerate(groups, 1):
        _print_group(index, group)
        if not group.qualified or group.suggested_rule is None:
            print("  candidate is not qualified for automatic JunkRule generation; skipping")
            continue
        preview = preview_rule(document, group.suggested_rule)
        _print_preview(preview)
        if _preview_is_broader(group, preview):
            print("  WARNING: preview is broader than the detected group; review before accepting.")
        while True:
            decision = input_fn("[a] accept [e] edit [s] skip: ").strip().lower()
            if decision == "a":
                accepted.append(group.suggested_rule)
                break
            if decision == "e":
                accepted.append(_edit_rule(input_fn, document, group))
                break
            if decision == "s":
                break
            print("ERROR: expected a, e, or s")

    _write_junk_config_contents(output_path, accepted)
    return tuple(accepted)


def write_junk_config(path: str | Path, rules: list[JunkRule] | tuple[JunkRule, ...]) -> None:
    """Write only accepted canonical JunkRules to a new JSON configuration."""
    output_path = Path(path)
    if output_path.exists():
        raise FileExistsError(f"inspection output already exists: {output_path}")
    _write_junk_config_contents(output_path, rules)


def _write_junk_config_contents(path: Path, rules: list[JunkRule] | tuple[JunkRule, ...]) -> None:
    payload = {
        "junk_rules": [
            {
                "target": rule.target,
                "matcher": rule.matcher,
                "pattern": rule.pattern,
            }
            for rule in rules
        ]
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _print_group(index: int, group: DetectionGroup) -> None:
    print(f"[{index}] {group.scope}: {group.pattern}")
    print(f"  occurrences: {group.occurrences}")
    print(f"  evidence: {', '.join(group.evidence)}")
    if group.suggested_rule is not None:
        print(
            "  suggested rule: "
            f"{group.suggested_rule.target}:{group.suggested_rule.matcher}:"
            f"{group.suggested_rule.pattern}"
        )


def _print_preview(preview: RulePreview) -> None:
    print(
        "  preview: "
        f"{preview.matched_count} matches, "
        f"{preview.affected_block_count} affected blocks"
    )
    if preview.examples:
        print(f"  examples: {preview.examples}")


# locations and occurrences share the same index domain (line number for
# line-scope groups, block index for block-scope groups).
def _preview_is_broader(group: DetectionGroup, preview: RulePreview) -> bool:
    return (
        preview.matched_count > len(group.occurrences)
        and not set(preview.locations).issubset(group.occurrences)
    )


def _edit_rule(
    input_fn: Callable[[str], str],
    document: PhysicalDocument,
    group: DetectionGroup,
) -> JunkRule:
    original = group.suggested_rule
    if original is None:
        raise ValueError("cannot edit an unqualified detection group")
    while True:
        value = input_fn(
            "rule TARGET:MATCHER:PATTERN "
            f"[{original.target}:{original.matcher}:{original.pattern}]: "
        ).strip()
        if not value:
            value = f"{original.target}:{original.matcher}:{original.pattern}"
        try:
            rule = parse_junk_rule(value)
            preview = preview_rule(document, rule)
        except (JunkRuleConfigurationError, ValueError) as exc:
            print(f"ERROR: invalid JunkRule: {exc}")
            continue
        print("  edited rule preview:")
        _print_preview(preview)
        if _preview_is_broader(group, preview):
            print("  WARNING: edited preview is broader than the detected group; review carefully.")
        return rule

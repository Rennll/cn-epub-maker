# DD-04 — Intermediate Semantics

## Status

Resolved.

## Decision

The Intermediate representation is a serialization and inspection artifact around the canonical in-memory `Book` model. It is not a second semantic model, runtime state, or independently rebuildable application artifact.

The current conversion pipeline treats `Book` as the canonical semantic representation between parsing and rendering. Intermediate serialization may expose that structured result for inspection, debugging, provenance, and future tooling, but the application does not require an Intermediate reader to continue a conversion.

Intermediate therefore does not currently promise arbitrary `Intermediate → Book` reconstruction, cross-version compatibility, migration, or a stable interchange-format contract.

## Current scope

Intermediate may contain:

- book-level metadata required to inspect the serialized result;
- chapter and volume structure derived from `Book`;
- serialized chapter content;
- transformation provenance/audit information when available.

The serialized representation should be internally consistent and should avoid presenting duplicate fields as independent sources of semantic truth. In particular, relationships between volume-owned chapters and the canonical chapter manifest must be explicit enough for inspection without requiring a reader to infer ownership from conflicting copies of chapter metadata.

Within `volumes[].chapters[]`, array order is the canonical chapter order within that volume. No additional ordering field is required.

The exact serialization shape remains an implementation concern unless a future requirement promotes Intermediate to a formal interchange format.

## Non-goals

This decision does not introduce:

- an Intermediate deserializer or rebuild API;
- an `Intermediate → Book` round-trip guarantee;
- schema versioning or migration support;
- backward-compatibility guarantees across arbitrary Intermediate artifacts;
- a new persistent domain model parallel to `Book`;
- source-text reconstruction from Intermediate.

These may be considered later as separate architecture work if the product needs Intermediate to become an independently consumable artifact.

## Relationship to the pipeline

The current structural boundary is:

```text
Parser → Book → Intermediate serialization → Renderer → EPUB
```

`Book` remains the semantic hand-off used by the application. Intermediate serialization is optional and is currently used as an inspectable artifact, including through `--keep-intermediate`.

A future workflow such as:

```text
Intermediate artifact → reader → Book → Renderer → EPUB
```

would constitute a new capability and must establish its own compatibility and schema contract before implementation.

## Relationship to #31

Issue #31 identifies ambiguity caused by describing chapters in both `volumes[].chapters[]` and the top-level `chapters` collection. DD-04 does not require preserving that redundancy merely because a future reader might need it.

The implementation should instead make the serialized relationship clear while keeping the change local to the current artifact format. The goal is to remove ambiguity for inspection and maintenance without turning Intermediate into a new rebuildable format.

## Reopen when

Revisit DD-04 if the project needs any of the following:

- rebuilding a `Book` without the original source text;
- consuming Intermediate from a separate process or tool;
- resuming EPUB generation from an Intermediate artifact;
- long-lived Intermediate files with compatibility guarantees;
- schema evolution or migration between Intermediate versions.

Any such requirement should be treated as a new architecture feature rather than being inferred from the current serialization format.

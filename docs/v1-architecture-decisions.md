# V1 Architecture and Decision Record

## Status

V1 baseline. Phase 1–6 are complete and the implementation has been merged into `main`.

This document records the decisions that define the V1 foundation. It is intentionally limited to decisions already made. Decisions about future feature extensions are not fixed here and should be discussed before being added to this document.

## V1 Goal

V1 is a minimal, text-preserving EPUB pipeline.

The goal is to establish a clean foundation from source TXT through an intermediate representation to EPUB, with explicit validation. V1 is not intended to fully reproduce the behavior of `cn-epub-maker` or to implement every transformation and formatting feature of the legacy implementation.

The guiding principle is to make the smallest necessary text changes for normalization and structural conversion while preserving the source text's meaning and content.

## Pipeline

The V1 pipeline is divided into six phases:

1. **Model** — `Book`, `Volume`, `Chapter`, and `Paragraph`, with defined serialization.
2. **Normalize** — encoding, BOM, newline normalization, and leading full-width-space handling.
3. **Parser** — TXT → `Book`, producing volumes, chapters, paragraphs, and warnings.
4. **Intermediate** — `Book` → `book.json` and `Chapter` → `chapters/*.json`.
5. **EPUB** — intermediate data → Markdown → Pandoc → EPUB, followed by the required EPUB package assembly.
6. **Validation** — parser validation, EPUB structural validation, and optional EPUBCheck.

Each phase has a defined responsibility. Later phases should not silently take over semantic work that belongs to an earlier phase.

## Model Decisions

The canonical internal representation is hierarchical:

`Book → Volume → Chapter → Paragraph`

The model is the boundary between parsing and rendering. Renderer code should consume the model rather than reimplementing TXT parsing rules.

Serialization is part of the model contract because the intermediate representation must be stable enough to support large books and independent chapter processing.

## Normalization Decisions

Normalization is deliberately conservative. It handles representation-level issues such as encoding, BOM, newline format, and the agreed leading full-width-space rule.

Normalization must not perform semantic rewriting of the source text. Text transformations that change wording, punctuation meaning, or language semantics are outside the V1 normalization contract.

## Parser Decisions

The parser converts normalized source text into the canonical Book hierarchy. It is responsible for identifying volumes, chapters, and paragraphs and for reporting non-fatal irregularities as warnings.

A condition that does not make the resulting EPUB structurally unsafe should normally be reported as a warning rather than preventing file generation. Fatal conditions are reserved for cases where the required output cannot be produced reliably.

## Intermediate Decisions

The intermediate representation separates parsing from EPUB rendering. `book.json` contains book-level information and hierarchy, while individual chapter JSON files allow chapter-scale data to be handled independently.

The design intentionally supports books with thousands of chapters without requiring the entire rendered document to be maintained as one monolithic intermediate artifact.

## EPUB Renderer Decisions

Pandoc is the preferred backend for text-to-EPUB conversion. The project supplies Pandoc with Markdown rather than asking it to understand the source TXT format directly.

The renderer owns the boundary between the internal model and the EPUB build process. Pandoc should perform work that it already handles well, including Markdown-to-HTML/XHTML conversion and EPUB generation. The project retains control over package-level requirements and the parts of the EPUB contract that need deterministic project-specific handling.

The V1 EPUB contract includes cover handling, metadata, TOC generation, volume/chapter hierarchy, CSS, manifest/spine consistency, and valid navigation targets.

The renderer must preserve source text as much as possible. Structural heading changes required to represent volume/chapter hierarchy are formatting transformations, not semantic rewriting.

## Validation Decisions

Validation has two layers.

The built-in validator checks the EPUB package structure and relationships that the project depends on, including `mimetype`, `META-INF/container.xml`, the container's OPF target, manifest targets, spine references, navigation targets, and related XML structure.

EPUBCheck is an additional external validator. It is an optional tool rather than a runtime dependency. If EPUBCheck is unavailable, built-in validation remains usable and the absence is reported as a warning. If EPUBCheck is available and reports validation errors, the validation command fails and exposes its diagnostic output.

Validation is not responsible for repairing source content. Its purpose is to report structural or output problems clearly.

## Warning vs Error Policy

V1 distinguishes between conditions that prevent reliable output and conditions that merely indicate unusual or imperfect input.

Non-fatal input irregularities should produce warnings while allowing EPUB generation to continue. This is important for the V1 objective of making minimal text changes rather than rejecting source material unnecessarily.

Structural failures that make the EPUB invalid or prevent the requested artifact from being produced are errors.

## CLI / Legacy Boundary

The new `novel_epub` pipeline is the V1 foundation. The legacy `cn_epub_maker.py` entry point remains in the repository for now.

V1 does not claim that the new pipeline is a complete behavioral replacement for the legacy implementation. Removing or migrating the legacy interface is a separate decision and should not be inferred from the V1 renderer refactor.

## Future Extensions

No future extension policy is fixed in this document yet. New features should be discussed in terms of their effect on the V1 contracts before implementation. In particular, an extension should identify whether it belongs in normalization, parsing, the model, intermediate representation, rendering, or validation, and whether it changes the text-preservation guarantee.

Until such a decision is made, V1 contracts should be treated as the baseline rather than opportunistically changed to accommodate new features.

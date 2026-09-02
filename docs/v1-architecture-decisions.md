# V1 Architecture

## Status

V1 is complete and is the stable baseline of the project. The Chinese chapter-number and preamble-preservation work is part of the V1 contract.

This document is the canonical description of V1 architecture and behavior. It records stable decisions rather than development history.

## Scope and Principles

V1 is a minimal, text-preserving TXT-to-EPUB pipeline. Its purpose is to provide a predictable foundation from source text to a valid EPUB without attempting to reproduce every behavior of the legacy implementation.

The core principle is conservative processing: make only the representation and structural changes required by the pipeline, preserve source content where possible, and warn rather than guess when input is ambiguous.

V1 does not perform semantic text transformations such as Simplified-to-Traditional conversion, automatic junk removal, global Arabic-numeral conversion, or chapter renumbering.

## Architecture

The stable pipeline is:

```text
TXT
 ↓
Normalize
 ↓
Parser
 ↓
Book
 ↓
Intermediate
 ↓
Markdown
 ↓
Pandoc
 ↓
EPUB
 ↓
Validation
```

Each stage has a defined responsibility. Parsing determines document structure; Intermediate separates parsing from rendering; the renderer produces the EPUB; validation reports output problems. Later stages should not silently take over semantic work belonging to earlier stages.

## Data Model

The canonical hierarchy is:

```text
Book → Volume → Chapter → Paragraph
```

The model is the boundary between parsing and rendering. Renderer code consumes the model rather than reimplementing TXT parsing rules.

`Book` contains title, author, language, optional cover, optional preamble, volumes, and top-level chapters. `iter_chapters()` provides a logical traversal over chapters regardless of whether they belong to a volume or directly to the book.

`Volume` represents an explicitly detected volume heading and keeps its structural `sequence`, parsed `number`, source `label`, `title`, and chapters.

`Chapter` contains:

```text
sequence
number
label
title
paragraphs
```

These fields are deliberately separate:

- `number` is the parsed numeric value of the heading. `第一章` and `第1章` both produce `1`.
- `label` preserves the source heading representation.
- `sequence` records structural discovery order and is independent of chapter numbering.

Therefore missing numbers, gaps, duplicates, and non-numeric extra chapters do not require structural renumbering.

## Parsing

### Normalization

Normalization handles representation-level concerns: input encoding, UTF-8 BOM, newline format, and the defined removal of leading full-width spaces used for indentation.

Normalization does not intentionally rewrite the meaning of source text.

### Volume and Chapter Structure

The default chapter grammar supports Arabic numerals, conventional Chinese numerals, supported units such as `章`, `集`, `篇`, and `回`, and optional titles. Examples include:

```text
第1章
第一章
第十章
第二十一章
第一章 開始
```

Chapter recognition is grammar-based. The parser does not infer structure from semantic hints.

### Chapter Numbers and Labels

Arabic numbers are stored directly. Supported Chinese numeral forms are converted deterministically by the separate numeral converter; unsupported or ambiguous forms are not guessed.

Representative forms include:

```text
一 → 1
十 → 10
十一 → 11
二十一 → 21
一百零一 → 101
一千零二 → 1002
一萬零三 → 10003
一億 → 100000000
兩百零三 → 203
〇 → 0
```

Traditional and simplified variants supported by the converter are treated equivalently where defined.

The distinction between `number`, `label`, and `sequence` is part of the parser contract. The parser never uses the numeric value as a substitute for source representation or structural order.

### Extra Chapters

Explicitly recognized forms such as:

```text
番外1
番外一
番外篇1
番外篇一
```

become ordinary `Chapter` objects with `number = None`, the source `label`, and their structural `sequence`.

Extra chapters participate in the volume/chapter structure and navigation. Ordinary prose containing `番外` is not treated as a chapter unless it matches the explicit chapter grammar.

### Preamble

Non-empty content before the first detected chapter is preserved as first-class `Book.preamble` content. Blank lines delimit preamble paragraphs.

The preamble flows through the complete pipeline:

```text
Parser
 ↓
Book.preamble
 ↓
Intermediate
 ↓
EPUB/text/preamble.xhtml
```

It appears before chapter content and is exposed in EPUB navigation. Its existence does not by itself produce a warning.

### Paragraphs

Consecutive non-empty lines form a paragraph. A blank line flushes the current paragraph. The same rule is used for chapter content and preamble content, while their resulting paragraphs remain separate in the model.

### Structural Sequence

Chapter sequence is a monotonically increasing discovery order, not a repaired chapter number. Duplicate numbers, missing numbers, gaps, and extra chapters are preserved in their actual structural order.

## Intermediate Representation

Intermediate separates parsing from EPUB rendering and provides a stable serialization boundary. Book-level information is stored in `book.json`; chapter-scale data is serialized independently so large books do not require one monolithic rendered artifact. When present, preamble content is serialized separately as `preamble.json`.

The representation is intended to support books with thousands of chapters and independent downstream processing without coupling the parser to EPUB-specific resources.

## EPUB Generation

Pandoc is the preferred EPUB backend. The project converts the internal representation to Markdown and lets Pandoc handle Markdown-to-XHTML/EPUB conversion, while the project retains control over package-level requirements and deterministic project-specific assembly.

The V1 EPUB contract includes:

- book metadata and optional cover;
- volume/chapter hierarchy and navigation;
- CSS and the required reading presentation;
- manifest/spine consistency;
- valid navigation targets;
- preamble placement before chapter content when present.

The EPUB ZIP package keeps `mimetype` uncompressed; other entries are deflated.

Pandoc subprocess diagnostics are captured as UTF-8 with replacement handling so platform-specific console encodings do not make otherwise valid builds fail.

## Validation

Validation has two layers.

The built-in validator checks required EPUB package structure and relationships, including `mimetype`, `META-INF/container.xml`, the OPF target, manifest targets, spine references, navigation targets, and related XML structure.

EPUBCheck is an optional external validator. If it is unavailable, built-in validation can still run and the absence is reported as a warning. If EPUBCheck is available and reports actual validation errors, validation fails and exposes its diagnostics.

Warnings describe non-fatal irregularities; errors describe conditions that prevent reliable output or a valid requested artifact.

Typical parser warnings include:

```text
duplicate_chapter_number
duplicate_volume_number
unparsed_chapter_number
suspicious_chapter_heading
no_chapters
```

Duplicate chapter numbers are preserved rather than renumbered. A chapter heading whose numeric portion cannot be deterministically parsed produces a warning rather than a guessed value. Suspicious headings may be reported without being promoted to chapters. A source with no detected chapters produces `no_chapters`.

## Guarantees and Non-goals

The following are guaranteed V1 behaviors:

- Arabic and supported conventional Chinese chapter numbers are parsed deterministically.
- Supported traditional/simplified Chinese numeral variants are handled by the numeral converter.
- Empty chapter titles are valid.
- Preamble content before the first chapter is preserved.
- Explicit extra chapters are preserved with `number = None`.
- Duplicate and non-contiguous chapter numbers are preserved and reported where applicable.
- Structural recognition does not rely on semantic guesses.
- Parser warnings do not automatically prevent generation when output remains trustworthy.

Known limitations and intentional non-goals include:

- year-style digit sequences such as `二〇二六` are not interpreted as conventional Chinese numerals;
- invalid or ambiguous numeral combinations are rejected rather than guessed;
- the parser does not infer chapters from arbitrary Chinese prose;
- chapter numbers are never automatically repaired or renumbered;
- V1 does not provide full Chinese-language semantic understanding;
- V1 does not migrate legacy content transformations such as OpenCC, automatic junk cleaning, quote conversion, or global Arabic numeral conversion.

The detailed exhaustive behavior belongs in tests and implementation; this document records the stable contract and its boundaries rather than the development history.

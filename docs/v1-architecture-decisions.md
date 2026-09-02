# V1 Architecture and Decision Record

## Status

V1 baseline. Phase 1–6 are complete and the implementation has been merged into `main`.

The Chinese chapter number and preamble preservation feature is part of the V1 contract.

This document records the architectural decisions, data model boundaries, parsing rules, intermediate representation, EPUB rendering behavior, validation policy, and known limitations of the V1 pipeline.

The implementation is intentionally conservative: the parser should recognize structures that can be identified by explicit grammar, while avoiding semantic guesses that may alter the source text or structure.

## V1 Goal

V1 is a minimal, text-preserving EPUB pipeline.

The goal is to establish a clean foundation from source TXT through an intermediate representation to EPUB, with explicit validation. V1 is not intended to fully reproduce the behavior of `cn-epub-maker` or to implement every transformation and formatting feature of the legacy implementation.

The guiding principle is to make the smallest necessary text changes for normalization and structural conversion while preserving the source text's meaning and content.

## Pipeline

The V1 pipeline is divided into six phases:

1. **Model** — `Book`, `Volume`, `Chapter`, and `Paragraph`, with defined serialization.
2. **Normalize** — encoding, BOM, newline normalization, and leading full-width-space handling.
3. **Parser** — TXT → `Book`, producing volumes, chapters, paragraphs, preamble content, and warnings.
4. **Intermediate** — `Book` → `book.json` and chapter/preamble JSON resources.
5. **EPUB** — intermediate data → Markdown → Pandoc → EPUB, followed by the required EPUB package assembly.
6. **Validation** — parser validation, EPUB structural validation, and optional EPUBCheck.

Each phase has a defined responsibility. Later phases should not silently take over semantic work that belongs to an earlier phase.

## Model Decisions

The canonical internal representation is hierarchical:

`Book → Volume → Chapter → Paragraph`

The model is the boundary between parsing and rendering. Renderer code should consume the model rather than reimplementing TXT parsing rules.

Serialization is part of the model contract because the intermediate representation must be stable enough to support large books and independent chapter processing.

### Book

A `Book` contains title, author, language, optional cover, optional preamble paragraphs, volumes, and top-level chapters.

`iter_chapters()` provides a single logical traversal over chapters regardless of whether a chapter belongs to a volume or directly to the book. This keeps downstream consumers independent from the parser's two possible chapter locations.

### Volume

A `Volume` represents an explicitly detected volume heading. It contains `sequence`, source `number`, `label`, `title`, and chapters belonging to that volume.

The volume number is kept separately from its display label and title.

### Chapter

A chapter contains:

```text
sequence
number
label
title
paragraphs
```

The separation between these fields is an explicit V1 decision.

`number` is the parsed numeric value of the chapter heading. For example, `第一章` and `第1章` both produce `number = 1`.

`label` preserves the source heading representation, such as `第一章`, rather than requiring downstream code to reconstruct it from `number`.

`sequence` represents the chapter's position in parsed book structure. It is deliberately different from `number`, so missing numbers, duplicate numbers, gaps, and non-numeric extra chapters can still retain their structural position.

For example:

```text
第一章
第三章
```

may produce:

```text
chapter 1: number=1, sequence=1
chapter 2: number=3, sequence=2
```

The parser does not assume that chapter numbers are contiguous.

## Normalization Decisions

Normalization is deliberately conservative. It handles representation-level issues such as encoding, BOM, newline format, and the agreed leading full-width-space rule.

Normalization must not perform semantic rewriting of the source text. Text transformations that change wording, punctuation meaning, or language semantics are outside the V1 normalization contract.

## Chapter Structure Decisions

### Supported chapter headings

The default chapter grammar supports Arabic numerals, conventional Chinese numerals, supported chapter units such as `章`, `集`, `篇`, and `回`, and optional titles.

Examples include:

```text
第1章
第一章
第十章
第二十一章
第100章
第一章 開始
第二十一章新的開始
```

Whitespace between `第`, the number, and the unit is tolerated according to the parser's normalization and regular expression rules.

### Chinese chapter numbers

Chinese chapter numbers are converted to integers before being stored in `Chapter.number`.

The conversion is implemented separately from the parser in `novel_epub/chinese_numerals.py` through:

```python
chinese_numeral_to_int(text: str) -> int | None
```

The function has a narrow responsibility: convert a supported Chinese numeral representation into an integer, or return `None` when the representation cannot be deterministically interpreted.

Representative supported forms include:

```text
一       → 1
十       → 10
十一     → 11
二十     → 20
二十一   → 21
一百     → 100
一百零一 → 101
一千零二 → 1002
一萬     → 10000
一萬零三 → 10003
一億     → 100000000
兩百     → 200
兩百零三 → 203
〇       → 0
```

Traditional and simplified variants defined by the converter are supported, including forms such as `兩 / 两`, `萬 / 万`, and `億 / 亿`.

The converter is deterministic rather than heuristic. This is important because chapter-number interpretation affects structural identity, and guessing an ambiguous expression could create an incorrect chapter structure.

### Extra chapters

V1 supports explicitly formatted extra chapters through a dedicated grammar, including forms such as:

```text
番外1
番外一
番外篇1
番外篇一
```

An extra chapter is represented as an ordinary `Chapter` with:

```text
number = None
label = source label
sequence = structural position
```

Extra chapters participate in the volume's chapter structure and downstream TOC without being assigned an artificial numeric chapter number.

For example:

```text
第一章
番外一
第二章
```

may produce:

```text
Chapter(sequence=1, number=1)
Chapter(sequence=2, number=None)
Chapter(sequence=3, number=2)
```

The parser does not classify arbitrary prose containing the word `番外` as a chapter. Structural classification requires recognizable structure rather than semantic hints.

## Parser Decisions

The parser converts normalized source text into the canonical `Book` hierarchy. It is responsible for identifying volumes, chapters, paragraphs, and preamble content and for reporting non-fatal irregularities as warnings.

The main parser entry point is:

```python
parse_lines(...)
```

It processes normalized input line by line while maintaining the current volume, current chapter, structural sequences, paragraph buffers, and preamble buffer.

The recognition order is conceptually:

```text
input line
   ↓
normalize
   ↓
blank line?
   ├─ yes → flush current paragraph
   └─ no
       ↓
volume heading?
   ├─ yes → create Volume
   └─ no
       ↓
chapter heading?
   ├─ yes → parse number and create Chapter
   └─ no
       ↓
extra chapter heading?
   ├─ yes → create Chapter(number=None)
   └─ no
       ↓
current chapter exists?
   ├─ yes → append to chapter paragraph
   └─ no → append to preamble
```

The ordering matters because a line must be classified structurally before it can become ordinary paragraph content.

### Number parsing

`_parse_number()` is the boundary between textual chapter headings and the numeric model.

Conceptually:

```text
raw chapter number
       ↓
_parse_number()
       ↓
Arabic integer OR Chinese numeral conversion
       ↓
Chapter.number
```

This keeps numeric interpretation separate from chapter-heading recognition and allows Arabic and Chinese chapter numbers to share the same chapter creation path.

### Paragraph handling

Paragraphs are accumulated from consecutive non-empty lines. A blank line flushes the current paragraph.

The same mechanism is used for chapter content and preamble content, but the resulting paragraphs are stored separately.

This preserves paragraph boundaries without requiring semantic rewriting.

### Chapter sequence

The parser maintains a separate monotonically increasing `chapter_sequence`. It reflects parser discovery order, not the numeric value extracted from the heading.

This is important for missing chapter numbers, duplicate chapter numbers, extra chapters, and gaps in numbering. The parser does not silently renumber the source.

## Preamble

V1 treats content before the first detected chapter as first-class book content.

A `Book` contains:

```text
preamble: list[Paragraph]
```

The parser accumulates non-empty lines before the first chapter into preamble paragraphs. Blank lines delimit paragraphs.

For example:

```text
這是前言第一段。

這是前言第二段。

第一章
正文
```

produces two preamble paragraphs followed by the first chapter.

The preamble does not generate a warning merely because it occurs before the first chapter.

The preamble flows through the complete pipeline:

```text
Parser
  ↓
Book.preamble
  ↓
Intermediate preamble.json
  ↓
EPUB preamble.xhtml
  ↓
TOC / spine
```

The generated EPUB places the preamble before chapter content.

## Intermediate Decisions

The intermediate representation separates parsing from EPUB rendering. `book.json` contains book-level information and hierarchy, while individual chapter JSON files allow chapter-scale data to be handled independently.

When preamble content exists, it is serialized as `preamble.json` with paragraph content represented independently from EPUB-specific resources.

The design intentionally supports books with thousands of chapters without requiring the entire rendered document to be maintained as one monolithic intermediate artifact.

## EPUB Renderer Decisions

Pandoc is the preferred backend for text-to-EPUB conversion. The project supplies Pandoc with Markdown rather than asking it to understand the source TXT format directly.

The renderer owns the boundary between the internal model and the EPUB build process. Pandoc should perform work that it already handles well, including Markdown-to-HTML/XHTML conversion and EPUB generation. The project retains control over package-level requirements and the parts of the EPUB contract that need deterministic project-specific handling.

The V1 EPUB contract includes cover handling, metadata, TOC generation, volume/chapter hierarchy, CSS, manifest/spine consistency, and valid navigation targets.

The renderer must preserve source text as much as possible. Structural heading changes required to represent volume/chapter hierarchy are formatting transformations, not semantic rewriting.

### Preamble rendering

When present, the preamble is rendered as:

```text
EPUB/text/preamble.xhtml
```

and is placed before chapter content in the EPUB reading order.

The EPUB navigation also exposes the preamble as a separate entry, so preservation at the model level is reflected in the final reading experience.

### EPUB package compression

The V1 package follows the EPUB ZIP requirement that `mimetype` is stored without compression. Other EPUB entries are deflated.

Renderer integration tests explicitly verify this packaging invariant.

### Pandoc subprocess encoding

Pandoc subprocess output is captured using UTF-8 with replacement handling for decoding errors. This avoids platform-dependent failures when diagnostic output contains characters that cannot be decoded using the Windows platform default encoding.

## Validation Decisions

Validation has two layers.

The built-in validator checks the EPUB package structure and relationships that the project depends on, including `mimetype`, `META-INF/container.xml`, the container's OPF target, manifest targets, spine references, navigation targets, and related XML structure.

EPUBCheck is an additional external validator. It is an optional tool rather than a runtime dependency. If EPUBCheck is unavailable, built-in validation remains usable and the absence is reported as a warning. If EPUBCheck is available and reports validation errors, the validation command fails and exposes its diagnostic output.

Validation is not responsible for repairing source content. Its purpose is to report structural or output problems clearly.

## Warning vs Error Policy

V1 distinguishes between conditions that prevent reliable output and conditions that merely indicate unusual or imperfect input.

Non-fatal input irregularities should produce warnings while allowing EPUB generation to continue. This is important for the V1 objective of making minimal text changes rather than rejecting source material unnecessarily.

Structural failures that make the EPUB invalid or prevent the requested artifact from being produced are errors.

Examples of parser warnings include:

```text
duplicate_chapter_number
duplicate_volume_number
unparsed_chapter_number
suspicious_chapter_heading
no_chapters
```

### Duplicate chapter numbers

Duplicate numeric chapter numbers generate a warning. Both chapters remain in structural sequence rather than silently discarding the later occurrence.

### Unparseable chapter numbers

If a line matches the chapter-heading grammar but its number cannot be converted into a supported integer, the parser emits an `unparsed_chapter_number` warning rather than assigning a guessed value.

### Suspicious headings

Lines that look like possible chapter headings but do not match the configured chapter grammar may generate a `suspicious_chapter_heading` warning. The warning exposes likely parser limitations without converting every suspicious line into a chapter.

### No chapters

If parsing finishes without detecting any chapters, the parser emits a `no_chapters` warning.

## Edge Cases

### Guaranteed Behavior

The following behavior is part of the V1 contract.

- Arabic chapter numbers such as `第1章`, `第10章`, and `第100章` are supported.
- Conventional Chinese chapter numbers such as `第一章`, `第十章`, `第二十一章`, `第一百零一章`, and `第一千零二章` are supported through deterministic conversion.
- Defined traditional and simplified Chinese numeral variants are supported.
- A chapter may have no title; an empty title is valid and does not by itself produce an `empty_chapter` warning.
- Non-empty content before the first chapter is preserved as preamble content.
- Blank lines delimit separate preamble paragraphs.
- Explicitly recognized extra-chapter headings become normal `Chapter` objects with `number = None` and retain their structural sequence.
- Duplicate chapter numbers are preserved but reported as warnings.
- Chapter numbers do not have to be contiguous.
- Ordinary prose containing chapter-like words such as `番外` is not classified as a chapter unless it matches the explicit grammar.

### Known Limitations / Non-goals

The following behaviors are intentionally not guaranteed by V1.

#### Year-style Chinese digit sequences

Forms such as `二〇二六` are not treated as conventional Chinese numeral expressions by the current converter.

Supporting this form would require a separate rule for digit-by-digit Chinese numerals rather than implicitly broadening the existing converter.

#### Invalid or ambiguous unit combinations

Forms such as:

```text
十百
一百百
一億萬
```

are rejected by the numeral converter rather than interpreted heuristically.

#### Semantic chapter inference

The parser does not attempt to infer chapters based on semantic meaning.

For example, it does not assume that `作者後記` is an extra chapter merely because it appears after regular chapters. Similarly, `番外` appearing inside ordinary prose does not automatically create a chapter.

#### Automatic renumbering

The parser does not repair missing or duplicate chapter numbers. It records the source structure and reports detectable irregularities.

#### Full Chinese-language understanding

The parser does not attempt to determine whether arbitrary Chinese text is a chapter heading using semantic inference. The V1 contract is grammar-based.

## Development and Testing Decisions

The feature was developed using a test-first approach.

The main test areas are:

```text
Chinese numeral conversion
        ↓
Parser structure
        ↓
Intermediate representation
        ↓
EPUB renderer integration
```

Representative tests cover:

- Chinese numeral conversion and invalid numeral forms;
- Arabic and Chinese chapter numbers;
- chapter titles and whitespace variations;
- unparseable and duplicate chapter numbers;
- preamble preservation and paragraph boundaries;
- extra chapters and extra chapters inside volumes;
- ordinary prose containing `番外`;
- empty chapter titles;
- EPUB preamble output;
- EPUB TOC and spine ordering;
- EPUB ZIP compression;
- Pandoc renderer integration.

The tests document both expected successful input and the boundaries of parser behavior.

## Architectural Lessons

### Preserve source structure before improving semantics

When the parser encounters uncertain input, preserving the source as text or reporting a warning is generally safer than guessing. This is particularly important for ebook conversion, where an incorrect chapter split can alter the reading experience.

### Separate source representation from derived values

`number`, `label`, and `sequence` represent different concepts and should not be collapsed into a single field. Derived structural information should not replace source information when both are useful.

### Keep parsing and rendering independent

The intermediate representation provides a stable boundary. Parser improvements should not require EPUB-specific logic, and renderer changes should not require reimplementing source parsing.

### Treat preservation as an explicit requirement

Preamble preservation demonstrates that content which is not part of the primary chapter structure may still be meaningful. The absence of a chapter classification does not imply that the content should be discarded.

### Keep edge cases explicit

Unsupported forms should be documented rather than silently accepted. A deterministic limitation is preferable to a heuristic conversion that produces apparently valid but incorrect structure.

## CLI / Legacy Boundary

The new `novel_epub` pipeline is the V1 foundation. The legacy `cn_epub_maker.py` entry point remains in the repository for now.

V1 does not claim that the new pipeline is a complete behavioral replacement for the legacy implementation. Removing or migrating the legacy interface is a separate decision and should not be inferred from the V1 renderer refactor.

## Future Extensions

Future work should continue to be evaluated by layer.

Potential extensions may include improvements to source normalization, Chinese numeral handling, parser grammar, metadata extraction, EPUB rendering, or validation.

Extensions should not silently change the V1 contract. In particular, improvements to Chinese text handling should remain separate from chapter-structure parsing unless they are required for structural correctness.

If a future feature substantially changes the assumptions recorded in this document, it should be recorded as a separate ADR rather than continuously expanding this document.

Until such a decision is made, V1 contracts should be treated as the baseline rather than opportunistically changed to accommodate new features.

## V1 Contract Summary

The V1 architecture can be summarized as:

```text
Source Text
    ↓
Conservative Normalization
    ↓
Grammar-based Parser
    ↓
Book / Volume / Chapter / Paragraph
    │
    ├── Chapter.number
    ├── Chapter.label
    ├── Chapter.sequence
    └── Book.preamble
    ↓
Intermediate Representation
    ↓
Pandoc + EPUB Package Control
    ↓
Validated EPUB
```

The central V1 principle is:

> Parse explicit structure deterministically, preserve source content, and warn rather than guess when structure is uncertain.

The Chinese chapter number and preamble work extends this principle without changing the overall V1 pipeline. Chinese numerals become a deterministic input representation for chapter numbers, while preamble content becomes an explicit part of the book model and EPUB reading order.

# V1 Architecture Decisions

## Status

V1 is complete and serves as the stable structural and EPUB baseline for the project. The Chinese chapter-number and preamble-preservation work is part of the V1 contract.

The overall system architecture is described in `architecture-overview.md`. This document records V1-specific architectural decisions and stable behavioral contracts rather than development history.

## Scope and Principles

V1 is a minimal, text-preserving TXT-to-EPUB foundation. Its purpose is to provide predictable structural parsing, a stable Intermediate representation, EPUB generation, and validation without attempting to reproduce every behavior of the legacy implementation.

The core principle is conservative processing: make only the representation and structural changes required by the pipeline, preserve source content where possible, and warn rather than guess when input is ambiguous.

V1 does not perform semantic text transformations such as Simplified-to-Traditional conversion, automatic junk removal, global Arabic-numeral conversion, or chapter renumbering.

## Data Model

The canonical hierarchy is:

```text
Book
 └── Volume
      └── Chapter
           └── Paragraph
```

`Book` contains title, author, language, optional cover, optional preamble, volumes, and top-level chapters. A book may contain both volume-contained chapters and top-level chapters. `iter_chapters()` traverses all chapters in structural order regardless of whether they belong to a volume.

`Volume` contains structural sequence, parsed/source number, source label, title, and chapters.

`Chapter` contains:

- `sequence`
- `number`
- `label`
- `title`
- `paragraphs`

`number` is the parsed numeric value; `label` is the source heading representation; `sequence` is the structural discovery order. Missing numbers, gaps, duplicates, and non-numeric extra chapters do not require renumbering.

## Parsing Decisions

### Normalization

The normalization layer decodes supported TXT encodings and normalizes line endings before parsing. Automatic encoding detection tries `utf-8-sig`, `utf-8`, `gb18030`, `gbk`, and `big5` in that order after BOM handling. Explicitly supplied encodings are also supported.

Newline forms `CRLF` and `CR` are normalized to `LF`. The line-level normalization removes only leading U+3000 IDEOGRAPHIC SPACE characters. It does not generally trim whitespace, collapse whitespace, or otherwise rewrite content.

Normalization provides predictable parser input but does not infer document structure.

### Volume and Chapter Structure

The default grammar recognizes volume headings using units such as `卷`/`部`/`冊`, and chapter headings using `章`/`集`/`篇`/`回`, with optional whitespace and titles. Custom volume/chapter patterns can be supplied through the parser interface.

Parsing is grammar-based and does not infer document structure from general prose.

### Chapter Numbers and Labels

Arabic numbers are parsed directly. Supported Chinese numerals are converted deterministically by the separate numeral converter. Unsupported or ambiguous forms are not guessed.

Representative supported forms include 一→1, 十→10, 十一→11, 二十一→21, 一百零一→101, 一千零二→1002, 一萬零三→10003, 一億→100000000, 兩百零三→203, and 〇→0. Traditional/simplified numeral variants supported by the converter are treated equivalently where defined.

The parsed `number` is derived data; the source `label` remains available so structural representation is not replaced by the numeric value.

### Extra Chapters

Explicit forms `番外1`, `番外一`, `番外篇1`, and `番外篇一` become ordinary Chapters with `number=None`, the source label, and a structural sequence. Ordinary prose containing `番外` is not treated as a chapter unless the explicit grammar matches.

### Parser Failure and Warning Semantics

Parser diagnostics distinguish between structurally suspicious input and a matched chapter-like heading whose number cannot be parsed. An `unparsed_chapter_number` warning means a chapter-shaped heading matched the relevant grammar but its number could not be converted, so no chapter is created from that heading. A `suspicious_chapter_heading` warning means a line appears chapter-like but does not satisfy the chapter grammar; it remains ordinary content rather than being guessed into a chapter. These cases are intentionally different because they imply different recovery behavior.

Other structural warnings such as duplicate chapter/volume numbers do not cause automatic renumbering.

### Preamble

Non-empty content before the first detected chapter becomes `Book.preamble`. Blank lines delimit preamble paragraphs. Preamble content flows through Parser → Book.preamble → Intermediate → `EPUB/text/preamble.xhtml`, is placed before chapter content, and is included in navigation. It does not itself produce a warning merely because it occurs before the first chapter.

### Paragraphs

Consecutive non-empty lines form one paragraph; a blank line flushes the paragraph. The same rule is used for chapter and preamble text, while the model keeps preamble paragraphs separate from chapter paragraphs.

### Structural Sequence

`sequence` records monotonic discovery order independently of chapter number. Duplicate, missing, gapped, and extra chapters are preserved in structural order.

## Intermediate Representation

Intermediate separates parsing from EPUB rendering and provides a stable serialization boundary. Its current on-disk layout is:

```text
intermediate/
├── book.json
├── preamble.json        (optional)
└── chapters/
    ├── 000001.json
    ├── 000002.json
    └── ...
```

`book.json` stores book metadata, volume structure, and chapter entries that reference the corresponding chapter files. Each chapter is serialized independently rather than embedding every paragraph into one large `book.json` document.

This chapter-per-file layout is intentional: it keeps the serialization boundary manageable for works with thousands of chapters and allows downstream tooling to inspect or process chapters independently without constructing one giant JSON document.

The V1 Intermediate representation preserves the information required to reconstruct the V1 book model. It is a serialization boundary, not merely a temporary cache format.

## EPUB Generation Decisions

Pandoc is the preferred EPUB backend. The internal representation is rendered to Markdown and passed to Pandoc, while the project retains control over package-level requirements and deterministic project-specific assembly.

The V1 EPUB contract includes metadata, optional cover handling, volume/chapter hierarchy and navigation, CSS, consistent manifest/spine relationships, valid navigation targets, and preamble placement before chapters. Package structure includes the required `META-INF/container.xml` relationship to the OPF package document; manifest and spine entries must remain consistent with generated resources.

The ZIP package keeps `mimetype` uncompressed and deflates other entries. Pandoc subprocess diagnostics are captured as UTF-8 with replacement handling so encoding problems in tool output do not corrupt the build process.

## Validation Decisions

Built-in structural validation checks EPUB package relationships such as the container, OPF, manifest, spine, navigation, and referenced resources. EPUBCheck is optional and provides additional standards validation.

The validation architecture has three layers: model validation of the structured `Book` before rendering, built-in EPUB package validation after generation, and optional external EPUBCheck validation. Missing EPUBCheck is a warning/optional condition; actual EPUBCheck errors fail validation. Warnings are nonfatal; errors indicate that the output cannot be treated as a reliably valid artifact.

Typical parser warnings include `duplicate_chapter_number`, `duplicate_volume_number`, `unparsed_chapter_number`, `suspicious_chapter_heading`, and `no_chapters`. Duplicate numbers are preserved. Unparseable numbers warn instead of guessing. Suspicious headings may be reported without becoming chapters. No chapters produces a warning.

## Guarantees

V1 guarantees that:

- Arabic and supported Chinese chapter numbers are deterministic;
- supported traditional/simplified numeral variants are handled by the converter;
- empty titles are valid;
- preamble is preserved;
- extra chapters are preserved with `number=None`;
- duplicate and non-contiguous numbers are preserved and reported where applicable;
- no semantic guesses are introduced;
- parser warnings do not automatically block otherwise trustworthy generation;
- the structured result can be serialized through Intermediate and rendered into a validated EPUB.

## Non-goals

V1 does not provide:

- semantic chapter inference;
- automatic renumbering;
- full Chinese semantic understanding;
- OpenCC conversion;
- automatic junk cleaning;
- quote/punctuation conversion;
- global Arabic numeral conversion;
- chapter renumbering;
- byte-for-byte source preservation;
- typography/layout semantics introduced by V2.x.

Year-style sequences such as `二〇二六` are unsupported, and invalid or ambiguous numerals are rejected rather than guessed.

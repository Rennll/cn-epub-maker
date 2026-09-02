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

TXT → Normalize → Parser → Book → Intermediate → Markdown → Pandoc → EPUB → Validation

Each stage has a defined responsibility. Parsing determines document structure; Intermediate separates parsing from rendering; the renderer produces the EPUB; validation reports output problems. Later stages should not silently take over semantic work belonging to earlier stages.

## Data Model

Canonical hierarchy: Book → Volume → Chapter → Paragraph.

Book contains title, author, language, optional cover, optional preamble, volumes, and top-level chapters. A book may contain both volume-contained chapters and top-level chapters. `iter_chapters()` traverses chapters regardless of whether they belong to a volume.

Volume contains structural sequence, parsed/source number, source label, title, and chapters.

Chapter fields:
- `sequence`
- `number`
- `label`
- `title`
- `paragraphs`

`number` = parsed numeric value; `label` = source heading representation; `sequence` = structural discovery order. Missing numbers, gaps, duplicates, and non-numeric extra chapters do not require renumbering.

## Parsing

### Normalization

The normalization layer handles source encoding, UTF-8 BOM, newline representation, and the defined leading full-width-space indentation. Parser matching also tolerates the whitespace forms covered by its grammar.

### Volume and Chapter Structure

The default grammar recognizes volume headings using units such as `卷`/`部`/`冊`, and chapter headings using `章`/`集`/`篇`/`回`, with optional whitespace and titles. Custom volume/chapter patterns can be supplied through the parser interface.

Parsing is grammar-based and does not infer document structure from general prose.

### Chapter Numbers and Labels

Arabic numbers are parsed directly. Supported Chinese numerals are converted deterministically by the separate numeral converter. Unsupported or ambiguous forms are not guessed.

Representative supported forms include 一→1, 十→10, 十一→11, 二十一→21, 一百零一→101, 一千零二→1002, 一萬零三→10003, 一億→100000000, 兩百零三→203, and 〇→0. Traditional/simplified numeral variants supported by the converter are treated equivalently where defined.

The parsed `number` is derived data; the source `label` remains available so structural representation is not replaced by the numeric value.

### Extra Chapters

Explicit forms `番外1`, `番外一`, `番外篇1`, and `番外篇一` become ordinary Chapters with `number=None`, the source label, and a structural sequence. Ordinary prose containing `番外` is not treated as a chapter unless the explicit grammar matches.

### Preamble

Non-empty content before the first detected chapter becomes `Book.preamble`. Blank lines delimit preamble paragraphs. Preamble content flows through Parser → Book.preamble → Intermediate → `EPUB/text/preamble.xhtml`, is placed before chapter content, and is included in navigation. It does not itself produce a warning merely because it occurs before the first chapter.

### Paragraphs

Consecutive non-empty lines form one paragraph; a blank line flushes the paragraph. The same rule is used for chapter and preamble text, while the model keeps preamble paragraphs separate from chapter paragraphs.

### Structural Sequence

`sequence` records monotonic discovery order independently of chapter number. Duplicate, missing, gapped, and extra chapters are preserved in structural order.

## Intermediate Representation

Intermediate separates parsing from EPUB rendering and provides a stable serialization boundary. It includes `book.json`, chapter-scale data serialized independently, and `preamble.json` when preamble content exists. The representation is intended to support works with thousands of chapters and downstream processing without coupling parsing to EPUB packaging.

## EPUB Generation

Pandoc is the preferred EPUB backend. The internal representation is rendered to Markdown and passed to Pandoc, while the project retains control over package-level requirements and deterministic project-specific assembly.

The V1 EPUB contract includes metadata, optional cover handling, volume/chapter hierarchy and navigation, CSS, consistent manifest/spine relationships, valid navigation targets, and preamble placement before chapters. Package structure includes the required `META-INF/container.xml` relationship to the OPF package document; manifest and spine entries must remain consistent with generated resources.

The ZIP package keeps `mimetype` uncompressed and deflates other entries. Pandoc subprocess diagnostics are captured as UTF-8 with replacement handling so encoding problems in tool output do not corrupt the build process.

## Validation

Built-in structural validation checks EPUB package relationships such as the container, OPF, manifest, spine, navigation, and referenced resources. EPUBCheck is optional and provides additional standards validation.

Missing EPUBCheck is a warning; actual EPUBCheck errors fail validation. Warnings are nonfatal; errors indicate that the output cannot be treated as a reliably valid artifact. Typical parser warnings include `duplicate_chapter_number`, `duplicate_volume_number`, `unparsed_chapter_number`, `suspicious_chapter_heading`, and `no_chapters`. Duplicate numbers are preserved. Unparseable numbers warn instead of guessing. Suspicious headings may be reported without becoming chapters. No chapters produces a warning.

## Guarantees and Non-goals

Guarantees: Arabic and supported Chinese chapter numbers are deterministic; supported traditional/simplified numeral variants are handled by the converter; empty titles are valid; preamble is preserved; extra chapters are preserved with `number=None`; duplicate and non-contiguous numbers are preserved and reported where applicable; no semantic guesses are introduced; parser warnings do not automatically block otherwise trustworthy generation.

Non-goals: year-style sequences such as `二〇二六` are unsupported; invalid or ambiguous numerals are rejected; there is no semantic chapter inference, automatic renumbering, or full Chinese semantic understanding; legacy transforms such as OpenCC, automatic junk cleaning, quote conversion, global Arabic numeral conversion, and chapter renumbering are outside V1.

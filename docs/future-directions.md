# Future Directions

## Writing Mode / Vertical Typesetting

Vertical writing is intentionally deferred. Do not implement it as part of the current typography/layout work unless a concrete requirement or observed reader problem makes it necessary.

### Architectural direction

- Keep writing direction as a renderer/output concern, not part of the core `Book`, `Chapter`, or `Paragraph` content model.
- Reserve a future render configuration concept such as:
  - `writing_mode = "horizontal-tb" | "vertical-rl"`
- The current/default mode remains `horizontal-tb`.
- Do not add an enum, dataclass field, CLI option, or configuration surface yet solely for this future capability.
- Prefer renderer-level or typography-level processing when vertical writing is eventually implemented.
- Keep the Intermediate representation layout-agnostic unless a concrete semantic requirement demonstrates that an inline/layout representation is necessary.

### Expected future concerns

When vertical writing is implemented, treat it as a typography/layout policy rather than simply adding `writing-mode: vertical-rl`. At minimum, evaluate:

- EPUB page progression and right-to-left progression for vertical books;
- CJK punctuation and glyph orientation;
- Latin text orientation;
- numeric runs and best-effort tate-chu-yoko / horizontal-in-vertical treatment;
- URL, email, and code handling;
- basic CJK line-breaking and prohibition rules;
- headings and navigation consistency;
- image orientation;
- explicit CJK font selection and fallback behavior;
- reader-specific compatibility and capability differences, especially Apple Books and Kindle/KDP;
- representative real-device validation before treating presentation behavior as stable.

### Content preservation

- Preserve source text when changing presentation mode.
- Do not convert Arabic numerals to Chinese numerals merely to make vertical presentation look better.
- Keep content normalization (OpenCC, punctuation normalization, junk cleanup) separate from vertical typography/orientation decisions.

### Historical note

The previous architecture implemented vertical writing through CSS plus post-generated EPUB ZIP/XML patching and reader-specific fixes. Future work should not reproduce that pattern. The current renderer already owns XHTML, CSS, OPF, navigation, and EPUB packaging, so vertical writing should be integrated at that boundary rather than by generating an EPUB and patching it afterward.

### Relationship to V2.1 typography/layout

The existing V2.1 typography/layout contracts remain horizontal-writing focused for now. Their semantic paragraph boundaries, Intermediate compatibility, and renderer responsibilities should not be changed merely to reserve vertical writing.

Vertical writing should be treated as a future output/presentation capability built on top of those stable semantic contracts.

## Future Book-Level Transforms / Annotations

The current text `TransformPipeline` is intentionally scoped to source-text normalization before parsing. Future features that operate on the parsed `Book` model may require a separate book-level transformation boundary between parsing/validation and rendering.

### Architectural direction

- Keep the existing text transform contract (`text -> text`) focused on source normalization and canonicalization.
- Do not turn the current `TransformPipeline` into a generic pipeline that accepts arbitrary object types merely to support future features.
- Reserve a future boundary conceptually as:
  - `Parser -> Book validation -> Book-level transforms/annotations -> Renderer`
- A book-level transform should operate on the semantic `Book` / `Chapter` / `Paragraph` model rather than on generated HTML, XHTML, or the final EPUB archive.
- Keep the `Book` content model independent of EPUB/HTML rendering unless a future feature demonstrates a concrete semantic need for additional representation data.
- Do not add empty annotation fields, interfaces, CLI options, or configuration surfaces solely to reserve this capability.

### Future annotation use cases

A future annotation feature may need to derive presentation-related information from already-parsed text while preserving the canonical source text. Zhuyin is one possible example, but no specific annotation system or implementation is committed here.

If such a feature is introduced, prefer a separation between:

1. semantic text and book structure;
2. feature-specific resolution or analysis;
3. an encoding/representation step;
4. the final renderer/output format.

For example, a future pronunciation feature should be able to resolve a character's reading without making the resolver depend directly on EPUB, HTML, CSS, a particular font, or a particular encoding mechanism such as IVS.

### Intermediate representation

The Intermediate representation should remain the canonical, layout-agnostic representation of the parsed book. It should not become a container for generated HTML/XHTML or other renderer-specific markup merely to support annotations or typography features.

If a future annotation requires information beyond plain text, first establish whether that information is genuinely semantic and belongs in the Intermediate model. Renderer-specific mechanisms should remain outside the canonical content representation.

### Renderer boundary

The renderer should consume the semantic book plus any deliberately defined, renderer-independent transformation/annotation results. It should not be responsible for discovering linguistic properties, resolving pronunciation, or performing unrelated content analysis.

This boundary also avoids reproducing the previous architecture's pattern of generating an EPUB and then reopening the EPUB to patch XHTML for a feature that could have been applied before rendering.

### Relationship to current V2.1 architecture

No implementation is required solely to reserve this future capability. The current text transformation pipeline, parser, semantic models, Intermediate serialization, and renderer boundaries should remain independently usable without annotations.

When a concrete annotation feature is eventually implemented, first introduce the smallest book-level extension point required by that feature. Do not generalize the architecture beyond demonstrated requirements.

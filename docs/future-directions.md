# Future Directions

This document records deliberately deferred capabilities that may become future architecture work. It is not a roadmap or implementation task list. A capability should move into active design only when a concrete requirement or observed problem justifies it.

## Writing Mode / Vertical Typesetting

Vertical writing is deferred. The current/default writing mode remains horizontal.

When this becomes necessary, treat writing direction as a renderer/output concern rather than part of the core `Book`, `Chapter`, or `Paragraph` model. Keep the Intermediate representation layout-agnostic unless a concrete semantic requirement demonstrates otherwise.

Future evaluation should cover, at minimum:

- EPUB page progression and right-to-left progression;
- CJK punctuation and glyph orientation;
- Latin text orientation and numeric runs;
- URL, email, and code handling;
- CJK line-breaking and prohibition rules;
- heading and navigation consistency;
- image orientation;
- font selection and fallback;
- reader compatibility and representative real-device validation.

Presentation changes should preserve semantic source text. Content transformations such as OpenCC, punctuation normalization, and junk cleanup remain separate from writing-mode decisions.

The previous implementation history involved generating an EPUB and then patching ZIP/XML/CSS output for vertical-writing and reader-specific behavior. Future work should instead integrate at the existing renderer/output boundary rather than reintroducing post-generation patching.

## Book-Level Transforms / Annotations

The current text `TransformPipeline` remains scoped to source-text normalization and canonicalization before parsing. If a future feature needs to operate on the parsed `Book`, introduce the smallest separate book-level transformation or annotation boundary required by that feature.

The intended direction is conceptually:

```text
Parser → Book validation → Book-level transform/annotation → Renderer
```

Such processing should operate on semantic `Book` / `Chapter` / `Paragraph` data rather than generated HTML/XHTML or the final EPUB archive. Do not generalize the existing text pipeline merely to reserve this capability, and do not add empty model fields, interfaces, CLI options, or configuration surfaces without a concrete requirement.

A future annotation feature may need feature-specific analysis or resolution while preserving canonical source text. Keep those concerns separate from EPUB/HTML/CSS and from renderer-specific encoding details.

## Intermediate → Book → EPUB Rebuilding

A future use case may require Intermediate to become a stable, independently rebuildable artifact for later Book/EPUB generation. This is deliberately deferred.

The current contract is defined by DD-04: Intermediate is a serialization/inspection artifact around the canonical `Book` model, not an independently rebuildable interchange format. A reader, round-trip guarantee, schema migration, or cross-version compatibility contract should be introduced only as a separate future decision when a concrete requirement requires it.

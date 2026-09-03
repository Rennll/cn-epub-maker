# Session Handoff

## Current State

V1 is complete and stable.

V2 is complete for its defined scope: the transformation pipeline, CLI orchestration, Intermediate transformation metadata, focused/integration tests, and real TXT → CLI → Pandoc → EPUB black-box validation are all in place.

V2 extends the V1 core rather than replacing it. The completed path is:

Normalize → V2 Transformations → Parser → Intermediate → V1 EPUB Renderer → Validation

The V2 design and migration decisions are recorded in `docs/v2-migration-and-design-decisions.md`. Source code and tests remain the canonical source for implementation details.

## Next Stage: V2.x Typography / Layout

The next stage is typography and layout evolution of the existing EPUB renderer. Treat this as V2.x work, not unfinished V2 work and not a reason to merge V1/V2 version boundaries.

The earlier idea of `Intermediate → Book → EPUB` rebuilding remains a separate possible future V2.x feature. It is not the current task and should not be pulled into typography/layout implementation.

This session finalized the architecture/specification direction only. No implementation or tests should be added from this handoff session. The next implementation session should use TDD: establish red tests first, let the user run CI and report the failure, then implement and verify incrementally.

## Core Architecture Decisions

### Book remains the domain model

`Book` remains the runtime core. Keep `Chapter.paragraphs: list[Paragraph]`; do not replace it with a generic `Block` hierarchy for this typography phase.

Typography/layout semantics must not be encoded as CSS values inside the domain model.

### Paragraph boundary semantics

The parser currently discards the number of consecutive blank lines. Typography/layout needs that information as a structural signal, so introduce a semantic paragraph boundary concept rather than preserving raw blank-line counts.

Preferred model:

```python
class ParagraphBoundary(Enum):
    NORMAL = "normal"
    EXPANDED = "expanded"
    SCENE_BREAK = "scene-break"

@dataclass
class Paragraph:
    text: str
    boundary: ParagraphBoundary = ParagraphBoundary.NORMAL
```

Use `boundary`, not `boundary_before`. `boundary_before` is too easy to interpret as CSS `margin-top` or a paragraph spacing value. `boundary` means the structural relationship between this paragraph and the preceding content.

`Paragraph.boundary` is semantic content structure. It is not a CSS property, spacing value, or raw source-format count.

The default must remain `NORMAL`, so existing `Paragraph("...")` construction remains compatible.

Parser mapping for source blank-line runs:

- 0 or 1 blank line between paragraphs → `NORMAL`.
- 2 blank lines → `EXPANDED`.
- 3 or more blank lines → `SCENE_BREAK`.

Do not preserve the exact raw count as a permanent domain field. The semantic categories are the contract.

Apply the same `Paragraph`/boundary semantics to preamble paragraphs for consistency. No separate preamble block model is needed.

### Intermediate compatibility

Intermediate remains an optional persisted artifact, not a required pipeline stage and not a new core interchange model.

Persist paragraph boundary semantics in Intermediate. Preserve the existing JSON shape for normal paragraphs where practical:

```json
{"text": "..."}
```

For non-default boundaries, add the semantic field:

```json
{"text": "...", "boundary": "expanded"}
{"text": "...", "boundary": "scene-break"}
```

When reading older Intermediate artifacts, a missing `boundary` field must mean `NORMAL`.

Do not redesign Intermediate beyond what is required to carry this semantic information.

## Renderer / Presentation Boundary

Keep the responsibility split explicit:

```text
Book semantic structure
        ↓
Renderer semantic HTML
        ↓
Typography/Layout presentation configuration
        ↓
CSS
        ↓
EPUB
```

The renderer may choose appropriate semantic HTML structure and CSS classes/markers for paragraph boundaries, chapters, and other presentation-relevant structure. CSS decides visual spacing and typography.

Renderer must not modify content semantics merely for presentation. In particular, it must not merge, split, rewrite, invent text, normalize punctuation, or insert spaces as part of layout.

For paragraph text containing `\n`, preserve the distinction between one Paragraph and multiple Paragraphs. Do not use sentence-length or punctuation heuristics to merge lines. The exact HTML representation of an intra-paragraph hard line break is a renderer concern, but it must not silently become a new semantic paragraph.

Use semantic markers/classes for `EXPANDED` and `SCENE_BREAK` rather than encoding the source blank-line count directly as repeated visual elements.

## Typography / Layout Configuration

Typography/layout values belong to the renderer presentation layer, not to `Book`, `Paragraph`, Parser, or transformation stages.

Initially, configuration may live directly in the renderer. If it becomes large enough to hurt readability, extract a small renderer-specific config module (for example `novel_epub/renderers/typography.py`). Do not build a general theme system.

Do not expose typography tuning as CLI options in this stage.

Candidate presentation parameters, not final contracts:

| Parameter | Candidate |
|---|---|
| Paragraph indent | `2em` |
| Line height | `1.7` |
| Paragraph margin | `0` |
| Horizontal page margin | `1–1.5em` |
| Vertical page margin | `1–2em` |
| Chapter title size | `1.3em` |
| Chapter title/body gap | about `1–2` text-line heights |
| Scene break visual gap | about `2–3` text-line heights |
| Chapter starts new page | yes |
| First chapter paragraph indented | yes |
| Writing direction | horizontal by default |
| Maximum content width | none |

These numbers are deliberately provisional. Final tuning requires actual EPUB output and validation on a phone and an approximately 6-inch e-reader.

## Typography / Layout Behavior

Paragraphs are the basic content unit. Use consistent indentation rather than preserving source full-width leading spaces; existing normalization behavior remains responsible for source indentation normalization.

Consecutive non-blank source lines remain separate paragraph content according to the existing parser model. Do not merge them based on sentence length, punctuation, or perceived prose flow.

Short paragraphs remain short. Do not automatically merge them.

Dialogue receives no special semantic type or heuristic styling. It uses the same paragraph indentation, line-height, and margins as normal prose.

Blank lines are structural signals, not literal blank paragraphs. One blank line is an ordinary paragraph boundary; two indicate expanded spacing; three or more indicate a scene break. Excessive blank runs are capped by the semantic mapping. Do not invent symbols such as `***` or `✦`.

The scene-break target of approximately 2–3 text lines is a visual result, not a requirement to emit three blank paragraphs or equivalent literal source content.

Chapter headings are left-aligned with moderate spacing and should avoid being stranded at the bottom of a reading page. Do not introduce a global widow/orphan management system in this phase.

Each chapter should begin on a new reading page. The existing architecture already emits chapter-level XHTML/spine entries, so this is primarily a renderer/CSS concern.

Volume names remain hierarchy/navigation information rather than independent reading content/pages.

Existing front matter such as title, author, cover, summary, foreword, and preface remains content in the existing model. No complex special styling system is required.

Do not force a specific Chinese font. The reader/user chooses the font; serif/sans-serif are conceptual presentation choices only.

Do not manually insert spaces between Chinese, English, or numbers. Future East Asian CSS spacing may be considered separately but is not required here.

Punctuation conversion remains a V2 transformation concern. The renderer must not perform independent punctuation normalization.

Use relative units for margins and typography. Do not use fixed pixel margins, fixed line counts, or a fixed maximum text width.

Default writing direction is horizontal. Leave architectural room for future vertical writing, but do not introduce vertical-specific rules now.

For long unbroken English/URL-like content, CSS should avoid obvious overflow where the EPUB reader supports the relevant wrapping behavior. This is presentation robustness, not a content transformation.

Default text alignment should remain left-aligned. Do not force full justification unless a later explicit decision is made. Chinese line breaking should be delegated to the EPUB/HTML/CSS engine rather than manually inserting line breaks.

Rich-text concepts such as lists, quotes, inline formatting, generic blocks, and semantic dialogue types are outside this phase because TXT does not provide reliable information for them. Revisit them only when a source format with reliable rich-text semantics requires it.

## Explicit Non-goals

Do not introduce:

- sentence-based line merging;
- automatic short-paragraph merging;
- dialogue heuristics or special dialogue classes;
- preservation of inconsistent source full-width spaces as typography;
- literal blank paragraphs for every source blank line;
- guessed scene-break symbols;
- renderer-side punctuation normalization;
- manually inserted Chinese/English/numeric spaces;
- forced fonts;
- fixed-pixel layout values;
- a fixed maximum text width;
- global widow/orphan management;
- a generic `LayoutEngine`;
- a generic `Block`/`Inline`/`RichText` model;
- a general `Theme` system;
- CLI typography tuning options.

Do not reopen completed V1/V2 transformation behavior merely to make typography convenient.

## Implementation / Validation Order for Next Session

1. Start with TDD. Add focused red tests for `ParagraphBoundary` and parser blank-run semantics. The user runs CI and reports the expected failure.
2. Implement the minimal domain/parser changes. The user runs CI and reports green.
3. Add/update Intermediate serialization tests and implementation, preserving backward interpretation of missing `boundary` as `NORMAL`.
4. Define the renderer semantic HTML representation for paragraph boundaries and chapter structure.
5. Centralize typography/layout parameters in the renderer or a small renderer-specific config module if needed.
6. Add renderer tests for semantic structure and CSS behavior.
7. Verify chapter new-page and heading pagination behavior through real EPUB generation rather than assuming CSS support.
8. Run black-box EPUB validation with representative content, including blank-run boundaries, hard line breaks, long URLs, chapters, and front matter.
9. Validate the actual EPUB on a phone and an approximately 6-inch e-reader.
10. Tune only a small number of global presentation parameters based on device results.

Do not implement or test `Intermediate → Book → EPUB` rebuilding as part of this typography/layout task.

## Session Boundary

This handoff records the finalized direction for the next V2.x typography/layout implementation session. This session intentionally did not implement production code or tests.

# V2.1 Typography and Layout Design

## Status

V2.1 Typography / Layout is the first V2.x architecture-evolution milestone. Its semantic baseline has been implemented and merged.

This document records the V2.1 design baseline for typography and layout. Real-device presentation tuning and cross-reader validation are follow-up work, not prerequisites for the semantic implementation to be considered complete.

The overall system architecture is described in `architecture-overview.md`. V2.1 makes only the semantic extension described here to the existing structural and rendering boundaries.

Typography and layout numeric values are candidate values for initial implementation and testing. They are not architectural contracts and may be adjusted after real-device testing.

## 1. Scope

V2.1 improves presentation while preserving the semantic content and structural guarantees established by V1 and V2.

The goals are:

- preserve paragraph and chapter semantics;
- represent meaningful differences in paragraph spacing without preserving raw blank-line counts;
- provide semantic information to the renderer for normal, expanded, and scene-break paragraphs;
- preserve hard line breaks within paragraphs;
- provide predictable EPUB pagination intent;
- keep presentation decisions separate from parsing and text transformation;
- preserve existing Intermediate artifacts and backward compatibility.

## 2. Non-goals

This work does not introduce:

- sentence-level semantic analysis;
- dialogue detection heuristics;
- automatic sentence merging or splitting;
- guessed scene-break symbols;
- literal blank HTML paragraphs;
- preservation of exact source blank-line counts;
- automatic chapter renumbering;
- global Arabic numeral conversion;
- renderer-side text rewriting or punctuation/OpenCC processing;
- a generic `LayoutEngine`;
- a generic `Theme` abstraction;
- fixed-pixel typography;
- reader-specific pagination hacks;
- CLI-level fine-grained typography tuning as a primary interface.

## 3. Semantic Model

The existing hierarchy remains:

```text
Book
 └─ Volume
     └─ Chapter
         └─ Paragraph
```

`Paragraph` gains a small semantic boundary field:

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

`boundary` describes the presentation relationship between this paragraph and the preceding paragraph within the same content region. It is not a representation of raw source formatting.

### 3.1 Boundary scope

Boundary semantics apply only between adjacent paragraphs within the same content region.

The preamble is its own content region. Chapters and volumes are structural boundaries and do not become `ParagraphBoundary` values. The transition from the preamble to the first chapter likewise does not inherit a paragraph boundary.

### 3.2 Paragraph text and line breaks

Consecutive non-empty source lines remain one paragraph. An embedded `\n` in `Paragraph.text` represents a hard line break within that paragraph and does not create another `Paragraph`.

For example:

```text
line A
line B
```

is one paragraph whose text contains `line A\nline B`.

A blank line separates paragraphs.

## 4. Source Layout Semantics

### 4.1 Normalize is the layout baseline

Paragraph-boundary presentation semantics originate from the layout present after `Normalize`.

The intended invariant is:

> Paragraph boundary presentation semantics originate from Normalize output; subsequent transforms must not alter the semantic structure of blank-line runs.

The parser may consume the transformed text directly; a second copy of Normalize output is not required.

### 4.2 Junk Cleaner invariant

The Junk Cleaner is a remove-only transform. It may remove targeted non-content lines or blocks, but must not remove, merge, or create paragraph-boundary blank-line runs as an unrelated cleanup side effect.

OpenCC and punctuation conversion likewise do not redefine blank-line structure.

### 4.3 Blank-line mapping

Raw blank-line counts are intentionally not persisted.

Within a content region:

| Blank lines between paragraphs | Semantic boundary |
|---|---|
| 0 or 1 | `normal` |
| 2 | `expanded` |
| 3 or more | `scene-break` |

The mapping preserves meaningful presentation differences without coupling the Intermediate representation to arbitrary source formatting.

The semantic boundary belongs to the paragraph following the blank-line run.

### 4.4 No raw blank-count persistence

The Intermediate representation stores the semantic value only. It does not store the original blank-line count.

## 5. Intermediate Representation

The Intermediate representation remains the stable serialization boundary between parsing and rendering.

### 5.1 Backward compatibility

Normal paragraphs may omit the `boundary` field:

```json
{"text": "A normal paragraph."}
```

is equivalent to:

```json
{"text": "A normal paragraph.", "boundary": "normal"}
```

When reading Intermediate data, a missing field means `normal`.

### 5.2 Valid values

The only legal values are:

```text
normal
expanded
scene-break
```

### 5.3 Invalid values

An invalid boundary value is a recoverable Intermediate data problem.

The reader should:

1. emit a warning;
2. treat that paragraph as `normal`;
3. continue processing the document.

An invalid boundary must not fail the entire pipeline. The user may correct the Intermediate data and rerun the pipeline when appropriate.

## 6. Renderer Contract

The renderer consumes semantic document information and converts it into EPUB-compatible HTML/CSS.

The renderer must not merge paragraphs, split paragraphs, rewrite paragraph text, normalize punctuation, perform OpenCC conversion, or infer missing scene breaks.

### 6.1 Paragraph HTML

Paragraphs are represented as semantic HTML paragraphs:

```html
<p>...</p>
<p class="paragraph-expanded">...</p>
<p class="paragraph-scene-break">...</p>
```

The exact class names are implementation details. The stable contract is that the three semantic states are distinguishable by the renderer output.

### 6.2 Hard line breaks

Embedded `\n` characters remain hard line breaks inside the same paragraph. The renderer may map them to the appropriate HTML representation, such as `<br />`, but must not turn them into separate `<p>` elements.

### 6.3 Chapter boundaries

Chapter boundaries remain structural. A chapter start may carry new-page pagination intent independently of `ParagraphBoundary`.

## 7. EPUB Pagination

EPUB 2-era implementations commonly relied on CSS `page-break-before`, `page-break-after`, and `page-break-inside`. Modern CSS fragmentation uses `break-before`, `break-after`, and `break-inside`.

V2.1 should prefer standard modern pagination properties while retaining legacy declarations where they provide useful compatibility with older reading environments.

The project contract is semantic pagination intent, not identical physical pagination on every reader. A chapter may express the intent to begin on a new page, but the actual reader controls page layout, viewport, font rendering, and pagination details.

Real-device testing is therefore required for presentation verification.

## 8. Typography and Layout Principles

Typography should prioritize readability, predictable relative spacing, EPUB compatibility, and semantic structure.

### 8.1 Units

Use relative units such as `em`, `rem`, and percentages. Fixed pixels should not be the foundation of the layout.

### 8.2 Paragraph indentation

Normal prose uses a relative first-line indentation.

Candidate initial value:

```css
text-indent: 2em;
```

### 8.3 Line height

Candidate initial value:

```css
line-height: 1.7;
```

### 8.4 Paragraph spacing

Spacing should be expressed through CSS, not inserted spaces or empty paragraphs.

Candidate initial ranges are approximately 1–1.5em for horizontal margins and 1–2em for ordinary vertical spacing.

### 8.5 Expanded paragraphs

`expanded` should be visibly more separated than `normal`. The exact amount is a presentation parameter.

### 8.6 Scene breaks

`scene-break` should provide a clearly perceptible narrative separation, initially around 2–3 lines of visual space. The renderer must not invent a decorative symbol unless such a symbol is explicitly part of the semantic content.

### 8.7 Chapter titles

Candidate initial values are approximately 1.3em for title size and 1–2 text lines of title/body separation. Chapter starts normally carry new-page pagination intent.

### 8.8 Alignment and fonts

Body text defaults to normal left alignment. The renderer does not force a font. Horizontal writing is the default assumption for the current scope.

### 8.9 Long content

The EPUB should avoid obvious horizontal overflow where standard HTML/CSS behavior permits it. Overflow must not be solved by modifying source text.

## 9. Stable Contracts vs. Tuning Parameters

Stable semantic contracts are:

- the three `ParagraphBoundary` values;
- blank-run semantic mapping;
- missing boundary means `normal`;
- invalid boundary warns and falls back to `normal`;
- raw blank counts are not persisted;
- embedded `\n` remains a hard line break;
- paragraph boundaries remain distinct from chapter boundaries;
- renderer preserves text and paragraph structure;
- chapter starts express new-page intent.

Provisional presentation parameters include indentation, line height, paragraph margins, expanded spacing, scene-break spacing, chapter title size, and title/body spacing.

Changing these values should not require changes to the semantic model or Intermediate schema.

## 10. Acceptance Criteria

1. Existing Intermediate paragraphs without `boundary` load successfully.
2. Missing `boundary` is interpreted as `normal`.
3. Only `normal`, `expanded`, and `scene-break` are valid values.
4. Invalid boundary values warn and fall back to `normal` without terminating the pipeline.
5. Blank-line structure is interpreted within the same content region.
6. Boundary semantics do not cross chapter, volume, or preamble boundaries.
7. Raw blank-line counts are not persisted.
8. Embedded `\n` does not create additional paragraphs.
9. Renderer preserves paragraph count and paragraph text.
10. Renderer does not merge, split, or semantically rewrite paragraphs.
11. The three boundary states are distinguishable in semantic HTML/CSS.
12. Chapter starts carry pagination intent.
13. Generated EPUB remains structurally valid.
14. Content remains preserved after the defined V2 transformations.

Real-device presentation testing is separate from semantic correctness and is used to tune provisional typography values.

## 11. Implementation and Testing Order

1. Add parser/domain tests for normal, expanded, scene-break, hard line breaks, and boundary resets.
2. Add `ParagraphBoundary` and the default `Paragraph.boundary` field.
3. Update Intermediate serialization and backward-compatible boundary parsing.
4. Add warning/fallback behavior for invalid Intermediate boundary values.
5. Render semantic paragraph classes/markers.
6. Introduce candidate typography CSS values.
7. Add renderer tests for boundary classes, hard line breaks, chapter pagination intent, and EPUB structure.
8. Generate representative EPUB files.
9. Run black-box structural/content validation.
10. Test representative real reading environments and tune presentation values without changing semantic contracts.

## 12. Explicit Design Summary

V2.1 treats typography as a rendering concern built on explicit semantic information.

The parser interprets source blank-line runs into three semantic boundary states. The Intermediate representation stores those states without retaining arbitrary raw blank counts. The renderer converts those states into semantic HTML/CSS while preserving document text and paragraph structure. Chapter pagination is expressed as standard EPUB/HTML/CSS intent rather than reader-specific behavior.

The architecture is intended to remain stable while presentation parameters are refined through real-device testing.

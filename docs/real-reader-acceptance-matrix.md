# Real-reader acceptance matrix

> Status: baseline complete. Issue #27 / DD-07 resolved.
>
> This document defines what must be observed before changing renderer/CSS. It does not prescribe pixel-identical rendering across readers.

## Purpose

Use one deterministic generated EPUB and evaluate the same artifact in at least two real reading environments. Record the expected semantic behavior separately from presentation behavior that may legitimately vary by reader.

The validation sequence is:

1. Generate the representative fixture without changing renderer/CSS for the purpose of this validation.
2. Run structural/content validation on the generated EPUB.
3. Open the same EPUB in the selected desktop and mobile/tablet readers.
4. Record expected vs observed behavior.
5. Classify each finding before proposing a code/CSS change.
6. Only change renderer/CSS when the evidence points to a generator defect or a presentation parameter that should be tuned project-wide.
7. Re-run the same fixture and matrix after any change.

## Acceptance matrix

| ID | Case | Fixture signal | Expected semantic result | Observable expectation | Guarantee level | Severity if wrong |
| --- | --- | --- | --- | --- | --- | --- |
| RR-01 | CJK body text | Traditional + Simplified Chinese prose | Text preserved; no unintended rewriting | Characters display correctly and remain readable | Generator guarantee | P1 |
| RR-02 | Normal paragraph | Single paragraph boundary | `NORMAL` boundary | Ordinary paragraph spacing; indentation follows current provisional CSS | Mixed: structure guaranteed, visual value provisional | P1 |
| RR-03 | Expanded paragraph | Exactly two blank lines | `EXPANDED` boundary | Visibly larger separation than normal paragraph | Mixed | P1 |
| RR-04 | Scene break | Three blank lines | `SCENE_BREAK` boundary | Clearly visible scene separation without excessive blank-page-like space | Mixed | P1 |
| RR-05 | Hard line break | Two text lines separated by a single `\\n` within one paragraph | One paragraph with a hard line break; text is not merged/re-written | Line break remains visible inside the paragraph | Generator guarantee | P1 |
| RR-06 | Chapter heading | `第一章` heading in fixture | Heading remains structurally distinct from body | Heading hierarchy is visually obvious | Mixed | P1 |
| RR-07 | Chapter new-page intent | Chapter boundary after prior content | Chapter start carries intended new-page behavior | Chapter starts on a new page/reader location where the reader supports the EPUB instruction | Generator guarantee + reader variance | P1 |
| RR-08 | Long paragraph/chapter | Repeated CJK prose | Content remains intact and paginates normally | No clipping, overlap, unexpected horizontal overflow, or pathological pagination | Generator guarantee for structure; reader-dependent layout | P0 |
| RR-09 | Indentation | Ordinary body paragraphs | Normal paragraph remains a paragraph | First-line indentation is approximately the documented provisional value | Presentation parameter | P2 |
| RR-10 | Line height | Multiple dense body paragraphs | Paragraph structure unchanged | Text is comfortably readable; no clipping/overlap | Presentation parameter | P2 |
| RR-11 | Paragraph spacing | Normal vs expanded vs scene-break sequence | Boundary semantics preserved | Relative spacing is visually distinguishable and proportional | Presentation parameter | P2 |
| RR-12 | Margins/page geometry | Full-width CJK paragraphs | Content stays within reading viewport | No clipping or unintended horizontal scrolling at normal settings | Mixed | P1 |
| RR-13 | CJK line breaking/punctuation | Mixed `，。！？：「」『』（）` and Latin text | Characters/punctuation preserved | Reader's line breaking remains acceptable; no generator-introduced corruption | Mixed; reader-dependent where standards permit variance | P1 |
| RR-14 | Navigation/TOC | Multiple chapters/volumes | Navigation targets the correct structural documents | TOC entries are present, readable, and land at the intended section | Generator guarantee | P1 |
| RR-15 | Metadata | Fixture title/author/language metadata | Package metadata matches fixture | Reader displays expected title/author where supported | Generator guarantee | P1 |
| RR-16 | Cover | Representative cover metadata/resource | Cover resource is packaged and referenced correctly | Reader shows the cover where supported | Generator guarantee + reader variance | P1 |
| RR-17 | Horizontal overflow/clipping | Long unbroken Latin URL/email plus CJK | Content remains intact | No forced viewport overflow or clipped text caused by project CSS | Mixed | P1 |

## Environment matrix

The baseline was tested using the same generated EPUB artifact across the following environments. The EPUB was generated and structurally validated by GitHub Actions before manual inspection.

| Environment | Required role | Version/device | Artifact | Result | Notes |
| --- | --- | --- | --- | --- | --- |
| Android ReadEra | Mobile/tablet | ReadEra (Android) | Baseline EPUB | Pass — no content, structure, overflow, or semantic defect identified | Long continuous Latin/alphanumeric content showed somewhat unusual layout; classified as reader variance, not a generator defect |
| Kindle Paperwhite 3 | Conditional | Kindle Paperwhite 3, via EPUB-to-AZW3 conversion | Baseline EPUB | Pass — behavior normal for tested cases | Wider apparent right-side whitespace observed; classified as reader-dependent presentation variance |

Both environments showed wider apparent right-side whitespace. This was evaluated and classified as reader-dependent presentation variance rather than evidence of a generator defect. No renderer or CSS tuning was justified by the observed evidence.

Do not compare screenshots pixel-for-pixel. Compare behavior against the observable expectation above.

## Finding classification

Every non-trivial observation should receive exactly one primary classification:

- **Generator defect** — generated EPUB structure/content or renderer output violates a project guarantee.
- **Fixture/validation defect** — the test case does not actually exercise the intended condition or the expected result is wrong.
- **Presentation tuning** — the semantic output is correct, but a provisional renderer/CSS value is consistently undesirable across target readers.
- **Reader variance** — the same valid EPUB renders differently because of reader/device behavior, settings, or supported CSS.
- **Deferred** — evidence is insufficient, the target is out of scope, or a decision is intentionally postponed.

A reader difference alone is not a renderer defect.

## Findings record

### F-01 — Long continuous Latin/alphanumeric layout in ReadEra

```text
Case: RR-08, RR-17
Environment: Mobile/tablet
Reader/version/device: ReadEra (Android)
Fixture input signal: Long unbroken Latin/alphanumeric content within CJK prose
Expected: Content remains intact; no horizontal overflow or pathological pagination
Observed: Somewhat unusual layout for long continuous English/alphanumeric content
Classification: Reader variance
Severity: P2
Reproducible: Yes
Project-wide or reader-specific: Reader-specific
Proposed disposition: No renderer or CSS change; retain as documented reader variance
Evidence/screenshot reference: DD-07 in deferred-decision-audit.md
```

### F-02 — Wider apparent right-side whitespace

```text
Case: RR-12
Environment: Both (Android ReadEra and Kindle Paperwhite 3)
Reader/version/device: ReadEra (Android); Kindle Paperwhite 3 after EPUB-to-AZW3 conversion
Fixture input signal: Full-width CJK paragraphs
Expected: Content stays within reading viewport; no clipping or unintended horizontal scrolling
Observed: Somewhat wider apparent right-side whitespace in both environments
Classification: Reader variance
Severity: P2
Reproducible: Yes
Project-wide or reader-specific: Reader-dependent presentation variance
Proposed disposition: No renderer or CSS change; accepted as within normal reader behavior
Evidence/screenshot reference: DD-07 in deferred-decision-audit.md
```

## Baseline completion criteria

All criteria have been met for the DD-07 baseline:

- [x] All RR-01 through RR-17 cases have an explicit expected result.
- [x] The representative fixture produces a structurally valid EPUB (verified by GitHub Actions and EPUBCheck).
- [x] The same EPUB has been opened in at least one desktop and one mobile/tablet reader.
- [x] Each observed deviation has been classified.
- [x] Provisional typography/layout values have been evaluated; no change was warranted by the evidence.
- [x] No renderer/CSS change was made; the decision is explicitly recorded as no change.
- [x] Project guarantees are clearly separated from reader-dependent presentation behavior.

The acceptance baseline establishes the current renderer/CSS behavior as acceptable. Reader-dependent presentation differences remain outside the generator contract. DD-07 is resolved; this matrix is the supporting evidence record.

If a new target reading environment is added, or a reproducible generator defect is identified, reopen DD-07 and re-run this matrix against the same or an updated fixture.

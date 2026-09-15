# Real-reader acceptance matrix

> Status: baseline definition for Issue #27 / DD-07.
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

The first baseline requires the same generated EPUB artifact to be tested in at least two environments:

| Environment | Required role | Version/device | Artifact | Result | Notes |
| --- | --- | --- | --- | --- | --- |
| Desktop reader | Required | Record exact reader + version | Same baseline EPUB | Pending | |
| Mobile/tablet reader | Required | Record exact app + version + device/OS | Same baseline EPUB | Pending | |
| Kindle | Conditional | Only if Kindle is an explicit project target | Same baseline EPUB | Not targeted unless decided | |

Do not compare screenshots pixel-for-pixel. Compare behavior against the observable expectation above.

## Finding classification

Every non-trivial observation should receive exactly one primary classification:

- **Generator defect** — generated EPUB structure/content or renderer output violates a project guarantee.
- **Fixture/validation defect** — the test case does not actually exercise the intended condition or the expected result is wrong.
- **Presentation tuning** — the semantic output is correct, but a provisional renderer/CSS value is consistently undesirable across target readers.
- **Reader variance** — the same valid EPUB renders differently because of reader/device behavior, settings, or supported CSS.
- **Deferred** — evidence is insufficient, the target is out of scope, or a decision is intentionally postponed.

A reader difference alone is not a renderer defect.

## Evidence record

For each finding, record:

```text
Case:
Environment:
Reader/version/device:
Fixture input signal:
Expected:
Observed:
Classification:
Severity:
Reproducible:
Project-wide or reader-specific:
Proposed disposition:
Evidence/screenshot reference:
```

## Baseline completion criteria

The real-reader baseline is complete when:

- all RR-01 through RR-17 cases have an explicit expected result;
- the representative fixture produces a structurally valid EPUB;
- the same EPUB has been opened in at least one desktop and one mobile/tablet reader;
- each observed deviation has been classified;
- provisional typography/layout values have been accepted, adjusted, or deferred based on evidence;
- any renderer/CSS change is traceable to one or more findings, or the decision is explicitly recorded as no change;
- high-value structural regressions remain covered by automated tests where practical; and
- project guarantees are clearly separated from reader-dependent presentation behavior.

DD-07 should remain open until these criteria are met. At that point the deferred-decision audit can be updated with the evidence and final disposition.

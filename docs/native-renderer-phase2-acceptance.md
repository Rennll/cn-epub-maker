# Native renderer Phase 2 reader acceptance

Issue #73 Phase 1 is implemented and merged. This document defines the manual reader acceptance pass for the native XHTML/EPUB 3 renderer.

The acceptance artifact is deliberately generated from the existing semantic `Book` model. It does not use the parser, so reader observations can be attributed to the renderer/package output rather than parser inference.

## Generate the deterministic artifact

From the repository root:

```bash
python3 scripts/generate_native_acceptance_epub.py /tmp/native-renderer-acceptance.epub
```

For cover acceptance, supply a representative image:

```bash
python3 scripts/generate_native_acceptance_epub.py \
  /tmp/native-renderer-acceptance.epub \
  --cover /path/to/cover.jpg
```

Then run the repository's structural validation:

```bash
novel-epub validate /tmp/native-renderer-acceptance.epub
```

If EPUBCheck is installed, also run:

```bash
novel-epub validate /tmp/native-renderer-acceptance.epub --require-epubcheck
```

The fixture intentionally contains:

- Traditional Chinese and punctuation;
- an explicit hard line break inside a paragraph;
- normal, expanded, and scene-break paragraphs;
- chapter headings and chapter boundaries;
- multiple volumes and cross-volume navigation;
- mixed CJK/Latin/numeric content;
- long unbroken Latin/alphanumeric content;
- a long CJK paragraph for pagination;
- preamble content;
- optional cover packaging.

## Reader acceptance procedure

Use exactly the same generated EPUB in each target reader. Do not regenerate it between readers.

The existing baseline matrix in [real-reader-acceptance-matrix.md](real-reader-acceptance-matrix.md) remains the semantic checklist. For the native renderer, pay particular attention to RR-01 through RR-17, especially:

| Case | What to verify |
| --- | --- |
| RR-01 | CJK characters and punctuation are preserved and readable |
| RR-02–04 | Normal, expanded, and scene-break spacing are visibly distinguishable |
| RR-05 | The explicit line break remains inside the same paragraph |
| RR-06–07 | Chapter headings are distinct and chapter starts honor new-page intent |
| RR-08, RR-17 | Long CJK and unbroken Latin content do not clip, overlap, or cause pathological horizontal overflow |
| RR-13 | CJK punctuation and mixed Latin text remain intact |
| RR-14 | Preamble, volumes, and chapters navigate to the intended XHTML files |
| RR-15 | Title, author, and language metadata are correct |
| RR-16 | The supplied cover is packaged and displayed where supported |

Do not treat pixel-level differences between readers as failures. The project contract is semantic correctness plus reasonable presentation; reader-specific layout behavior should be recorded separately.

## Record findings

For every non-trivial observation, classify it as one of:

- Generator defect
- Fixture/validation defect
- Presentation tuning
- Reader variance
- Deferred

Only generator defects or consistently undesirable project-wide presentation values should lead to renderer/CSS changes.

For each finding, record the reader, version/device, exact case, expected behavior, observed behavior, classification, severity, reproducibility, and proposed disposition.

## Completion criteria for #73 Phase 2

Phase 2 is complete when:

1. The deterministic native-renderer artifact passes built-in structural validation.
2. EPUBCheck passes when available.
3. The same artifact has been opened in at least two real reading environments, preferably including one mobile/tablet reader and one desktop or dedicated e-reader.
4. RR-01 through RR-17 have been observed or explicitly marked not applicable.
5. Every non-trivial deviation has been classified.
6. Any generator defect found during manual acceptance is converted into an automated regression test before being fixed.
7. Reader-specific presentation differences are documented rather than encoded as arbitrary renderer workarounds.

After this pass, the project can make the separate decision about whether the native renderer is ready to expose as a public CLI/configuration option.
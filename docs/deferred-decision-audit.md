# Deferred Decision Audit

## Status

This document is the decision register for architectural and behavioral questions intentionally tracked during V2 and V2.x work. It records each decision's status, canonical source, and the condition under which it should be revisited.

Detailed technical definitions belong to the canonical documents referenced by each decision. This document is not an architecture document and not an implementation task list.

The audit covers DD-01 through DD-14. DD-15 is maintained in `future-directions.md` because it describes a future architecture direction rather than a current decision requiring an audit entry.

## Decision Status

| ID | Decision | Status | Canonical source |
| --- | --- | --- | --- |
| DD-01 | Configuration Model | Resolved | `v2x-configuration-model.md` |
| DD-02 | JunkCleaner rule input | Resolved | `junk-rule-configuration.md` |
| DD-03 | JunkCleaner default rules | Resolved | `dd-03-junkcleaner-default-rules.md` |
| DD-04 | Intermediate semantics | Resolved | `dd-04-intermediate-semantics.md` |
| DD-05 | Paragraph mode vs. source-format profile | Resolved | `v2x-configuration-model.md` |
| DD-06 | Normalize vs. Transformer responsibility | Resolved | `v2x-configuration-model.md` |
| DD-07 | Real-device typography completion criteria | Resolved | `real-reader-acceptance-matrix.md` |
| DD-08 | EPUBCheck role | Resolved | `dd-08-epubcheck-validation-policy.md` |
| DD-09 | Output filename sanitization and overwrite policy | Resolved | `dd-09-output-destination-policy.md` |
| DD-10 | Encoding auto-detection guarantee and positioning | Resolved | `normalize.py` + `v2x-configuration-model.md` |
| DD-11 | Automatic chapter renumbering | Frozen | This register |
| DD-12 | Generic semantic chapter inference | Frozen | This register |
| DD-13 | Punctuation/sentence-length paragraph splitting | Frozen | This register |
| DD-14 | Global Arabic numeral conversion | Frozen | This register |

## How to Read This Audit

A **Resolved** decision has a stable architectural answer. Implementation work may continue without reopening the decision unless the stated reopen condition is met.

A **Frozen** decision is an explicit non-goal or invariant. Reintroducing it requires a deliberate architectural revision.

---

## DD-01 — Configuration Model

**Status: Resolved**

Use `v2x-configuration-model.md` as the canonical definition of `ConversionRequest`, policy objects, configuration precedence, and the request/runtime boundary.

**Reopen when:** the current request/policy boundary can no longer represent a required configuration surface.

---

## DD-02 — JunkCleaner Rule Input

**Status: Resolved**

Use `junk-rule-configuration.md` as the canonical definition of the `JunkRule` model, structured configuration, CLI shorthand, ordering, validation, and merge semantics.

**Reopen when:** the canonical rule model, input forms, ordering, validation contract, or configuration-source merge semantics must change.

---

## DD-03 — JunkCleaner Default Rules

**Status: Resolved**

Use `dd-03-junkcleaner-default-rules.md` as the canonical decision. The application-level global `junk_rules` default remains empty; source-specific profiles and detection/candidate-generation workflows are outside this decision.

**Reopen when:** strong cross-source evidence establishes a safe global rule set, or the architecture introduces source-profile scoping that can safely support such rules.

---

## DD-04 — Intermediate Semantics

**Status: Resolved**

Use `dd-04-intermediate-semantics.md` as the canonical decision. Intermediate is a serialization/inspection artifact around the canonical in-memory `Book`; it is not an independently rebuildable interchange format or second semantic model.

**Reopen when:** the project needs to rebuild `Book` from Intermediate, consume Intermediate from another process/tool, resume EPUB generation from it, or provide long-lived compatibility guarantees.

---

## DD-05 — Paragraph Mode vs. Source-Format Profile

**Status: Resolved**

`paragraph_mode` remains part of `ParserPolicy`; a separate source-format profile abstraction is not introduced. The configuration model is canonical.

**Reopen when:** multiple source-specific behaviors must be selected as a coherent profile.

---

## DD-06 — Normalize vs. Transformer Responsibility

**Status: Resolved**

Normalization remains system-defined input interpretation; policy-driven transformations run after normalization. The configuration model is canonical.

**Reopen when:** a new behavior cannot be clearly classified as input interpretation versus user-selectable transformation policy.

---

## DD-07 — Real-Device Typography Completion Criteria

**Status: Resolved**

Use `real-reader-acceptance-matrix.md` and `v2x-typography-and-layout.md` as the canonical acceptance and typography references. The current baseline is accepted within the documented reader matrix, while reader-dependent presentation differences remain outside the generator contract.

**Reopen when:** a reproducible generator/content defect or project-wide presentation problem appears, or a new target reader/environment becomes an explicit requirement.

---

## DD-08 — EPUBCheck Role

**Status: Resolved**

Use `dd-08-epubcheck-validation-policy.md` as the canonical validation policy. It defines the boundary between built-in validation, optional local EPUBCheck validation, and strict CI/release validation.

**Reopen when:** the local/release conformance boundary changes or a different external conformance tool is adopted.

---

## DD-09 — Output Filename Sanitization and Overwrite Policy

**Status: Resolved**

Use `dd-09-output-destination-policy.md` as the canonical destination and filename contract, including automatic versus explicit destinations, sanitization, collision handling, and runtime reporting.

**Reopen when:** an explicit overwrite/force policy, destination derivation contract, or new platform filename requirement is introduced.

---

## DD-10 — Encoding Auto-Detection Guarantee and Positioning

**Status: Resolved**

Use `novel_epub/normalize.py` and `v2x-configuration-model.md` as the current canonical references. Auto-detection occurs at the input/runtime boundary with the documented BOM handling and deterministic candidate order; the selected codec is runtime/provenance state and does not mutate the request.

**Reopen when:** real-world inputs show that the supported candidate set or ordering is insufficient and require a new detection policy.

---

## DD-11 — Automatic Chapter Renumbering

**Status: Frozen**

Do not automatically renumber chapters. Preserve source structure unless a future requirement explicitly introduces structural normalization.

---

## DD-12 — Generic Semantic Chapter Inference

**Status: Frozen**

Do not introduce generic semantic chapter inference as an implicit conversion heuristic. Reopen only through an explicit product requirement with a defined inference contract.

---

## DD-13 — Punctuation / Sentence-Length Paragraph Splitting

**Status: Frozen**

Do not split paragraphs implicitly from punctuation or sentence length. Reopen only through an explicit parsing requirement with a defined semantic contract.

---

## DD-14 — Global Arabic Numeral Conversion

**Status: Frozen**

Do not perform global Arabic numeral conversion as an implicit transformation. Reopen only through an explicit transformation policy defining its scope and semantics.

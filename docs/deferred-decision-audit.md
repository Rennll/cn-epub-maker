# Deferred Decision Audit

## Status

This document is the decision register for architectural and behavioral questions that were intentionally left open, partially resolved, resolved, or frozen during V2 and V2.x work. It records decision status, current position, provenance, and conditions for revisiting a decision.

Detailed technical definitions belong to the canonical documents referenced by each decision. This document should not duplicate architecture documentation or serve as an implementation task list.

The audit currently covers DD-01 through DD-14. DD-15 has been moved to `future-directions.md` because it describes a future architecture direction rather than a current decision that needs tracking.

## Decision Status

| ID | Decision | Status | Primary dependency |
| --- | --- | --- | --- |
| DD-01 | Configuration Model | Resolved | Application architecture |
| DD-02 | JunkCleaner rule input | Open, ready to decide | Configuration Model |
| DD-03 | JunkCleaner default rules | Open, ready to decide | Configuration Model + DD-02 |
| DD-04 | Intermediate semantics | Partially resolved | Configuration Model + provenance model |
| DD-05 | Paragraph mode vs. source-format profile | Resolved | Parser architecture |
| DD-06 | Normalize vs. Transformer responsibility | Resolved | Configuration Model + stage boundaries |
| DD-07 | Real-device typography completion criteria | Open | EPUB rendering behavior |
| DD-08 | EPUBCheck role | Open | Release/CI policy |
| DD-09 | Output filename sanitization and overwrite policy | Resolved | Destination/CLI policy |
| DD-10 | Encoding auto-detection guarantee and positioning | Resolved | Input policy + runtime behavior |
| DD-11 | Automatic chapter renumbering | Frozen | Structural preservation |
| DD-12 | Generic semantic chapter inference | Frozen | Parser conservatism |
| DD-13 | Punctuation/sentence-length paragraph splitting | Frozen | Paragraph semantics |
| DD-14 | Global Arabic numeral conversion | Frozen | Transformation conservatism |

## How to Read This Audit

A decision marked **Resolved** has a stable architectural answer and should not be reopened merely because implementation remains incomplete.

A decision marked **Partially resolved** has a stable architectural direction, but one or more operational or implementation-level questions remain.

A decision marked **Open, ready to decide** has enough architectural foundation to make the remaining product or behavior decision without changing the Configuration Model.

A decision marked **Frozen** is an explicit non-goal or invariant. It should not be reintroduced through convenience heuristics or implementation shortcuts without a deliberate architectural revision.

---

## DD-01 — Configuration Model

**Status: Resolved**

### Decision

V2.x uses `ConversionRequest` as the application-level conversion request, with configuration expressed through typed policy objects. CLI-specific arguments and runtime execution state remain outside the request model.

### Canonical

`v2x-configuration-model.md`

### Evidence

V2.x configuration/resolver implementation and architecture tests.

### Reopen when

The current request/policy boundary can no longer represent the required configuration surface.

---

## DD-02 — JunkCleaner Rule Input

**Status: Open**

### Question

How should users define and provide `JunkRule` entries?

### Current position

The typed `JunkRule` schema belongs under `JunkCleanerConfig.rules`. The remaining decision concerns the public loading/input mechanism.

### Decision needed

- external configuration representation;
- CLI shorthand, if any;
- ordering guarantees;
- malformed-rule behavior;
- invalid-regex behavior;
- representation of rule provenance in transformation audit.

### Canonical

`novel_epub/transforms.py`

### Related

`v2x-configuration-model.md`

### Resolve when

The public rule schema and loading path are documented, implemented, and covered by tests.

---

## DD-03 — JunkCleaner Default Rules

**Status: Open**

### Question

Should JunkCleaner provide built-in default rules, and if so, which rules are safe enough to enable by default?

### Decision principles

Default rules must have strong evidence that they identify non-content material. Rules with plausible 正文 false positives should not be enabled globally.

### Decision needed

- default set;
- whether defaults can be disabled;
- whether user rules replace or extend defaults;
- whether source-specific defaults require a future source profile;
- provenance of default rules.

### Resolve when

The default set, precedence, safety rationale, and regression coverage are documented.

---

## DD-04 — Intermediate Semantics

**Status: Partially resolved**

### Question

What semantic contract should the Intermediate representation provide?

### Current decision

Intermediate is the structured serialization boundary around `Book` plus transformation provenance. It is not runtime state, raw source text, or a second configuration model.

### Remaining question

Whether Intermediate should become a stable, independently rebuildable artifact with a stronger semantic and compatibility contract.

### Canonical

`architecture-overview.md`

### Related

`future-directions.md`

### Evidence

Current Intermediate serialization and provenance/audit model.

### Resolve when

The required serialized fields, provenance semantics, and compatibility expectations are sufficiently defined for the intended scope.

---

## DD-05 — Paragraph Mode vs. Source-Format Profile

**Status: Resolved**

### Decision

`paragraph_mode` remains part of `ParserPolicy`. A separate source-format profile abstraction is not introduced.

### Canonical

`v2x-configuration-model.md`

### Evidence

V2.x parser policy, resolver validation, and regression coverage.

### Reopen when

Multiple source-specific behaviors need to be selected as a coherent profile.

---

## DD-06 — Normalize vs. Transformer Responsibility

**Status: Resolved**

### Decision

Normalization is system-defined input interpretation and is not part of user-configurable transformation policy. Policy-driven transformations run after normalization.

### Canonical

`v2x-configuration-model.md`

### Evidence

V2.x execution boundary and normalization/transformation tests.

### Reopen when

A new normalization behavior cannot be clearly classified as inherent input interpretation rather than user-selectable transformation policy.

---

## DD-07 — Real-Device Typography Completion Criteria

**Status: Open**

### Question

What evidence is sufficient to declare EPUB typography and layout complete?

### Decision needed

Define a repeatable acceptance matrix covering representative readers and at least:

- paragraph and line spacing;
- heading hierarchy;
- margins and page geometry;
- long chapters;
- CJK rendering;
- punctuation and line breaking;
- metadata, cover, and navigation.

### Resolve when

The project has a documented acceptance matrix and can distinguish implementation defects from reader-specific rendering differences.

---

## DD-08 — EPUBCheck Role

**Status: Open**

### Question

What role should EPUBCheck play in the conversion and release workflow?

### Current distinction

Built-in structural validation and EPUBCheck serve different levels of validation.

### Decision needed

Determine which checks are:

- required for normal conversion;
- recommended during development;
- required for release/CI.

### Resolve when

The project's validation and release policy explicitly defines the role of EPUBCheck.

---

## DD-09 — Output Filename Sanitization and Overwrite Policy

**Status: Resolved**

### Decision

Automatic destinations are derived from `<title>_<author>.epub` and placed beside the source. The derived filename is sanitized before use: path separators and platform-invalid filename characters with safe full-width equivalents are replaced, unsafe control characters are removed, and leading/trailing whitespace and `.` are removed. Empty or otherwise unusable names fall back deterministically to `book.epub`.

Automatic destinations never overwrite an existing EPUB. Collisions use deterministic numeric suffixes such as `book (01).epub`, `book (02).epub`, and selection occurs at execution time immediately before output creation.

Explicit destinations are a separate mode. They are not metadata-sanitized or silently renamed; invalid/unusable paths and existing destinations fail rather than being redirected or overwritten. Missing parent directories are not implicitly created.

Automatic sanitization or collision changes must be exposed through runtime reporting, while the actual selected output path is exposed through `ExecutionResult.epub_path`. These runtime facts do not mutate `ConversionRequest`.

### Canonical

`dd-09-output-destination-policy.md`

### Related

`v2x-configuration-model.md`

`novel_epub/configuration_resolver.py`

### Evidence

The DD-09 policy document defines automatic versus explicit destination semantics, sanitization, fallback naming, collision handling, parent-directory behavior, and reporting requirements.

### Reopen when

A future requirement introduces an explicit overwrite/force policy, a different destination derivation contract, or a supported platform whose filename rules cannot be represented by the current policy.

---

## DD-10 — Encoding Auto-Detection Guarantee and Positioning

**Status: Resolved**

### Decision

`encoding=auto` is resolved at the input/runtime boundary, after `ConversionRequest` resolution and before transformations, parsing, analysis, rendering, or validation. The resolver does not perform detection.

Detection first checks for the UTF-8 BOM. If the byte stream starts with the UTF-8 BOM, the selected encoding is `utf-8-sig`. This is a dedicated BOM check, not a general candidate-order entry, because Python's `utf-8-sig` codec also successfully decodes ordinary UTF-8 without a BOM.

For non-BOM input, the supported auto-detection candidate order is fixed and deterministic:

1. `utf-8`
2. `gb18030`
3. `gbk`
4. `big5`

The first non-BOM candidate that successfully decodes the complete byte stream is selected.

This is a practical candidate-based guarantee, not a general-purpose encoding detector. In particular, some legacy Chinese encodings are technically decodable by more than one codec. The implementation does not use semantic or language heuristics to decide whether the decoded text is linguistically correct. The documented priority order is the tie-breaker for non-BOM ambiguity.

If no supported candidate decodes the source, execution stops immediately with an explicit encoding-detection failure. Downstream transformation, parsing, analysis, rendering, and EPUB validation do not run. Explicitly requested encodings are decoded directly and do not silently fall back to auto-detection.

The requested value remains `ConversionRequest.policy.encoding` (for example, `"auto"`). The selected codec is runtime/provenance information exposed through `ExecutionResult.encoding` and is never written back into the request.

### Supported scope

The supported automatic inputs cover common UTF-8 and Chinese legacy TXT inputs: UTF-8, UTF-8 with BOM, GB18030/GBK-family data, and Big5. The policy does not claim reliable identification of every historical, malformed, mixed, or ambiguous Chinese encoding.

### Canonical

`novel_epub/normalize.py`

### Related

`v2x-configuration-model.md`

`novel_epub/execution.py`

### Evidence

Runtime normalization tests cover UTF-8, UTF-8 BOM, GB18030, explicit Big5 decoding, deterministic multi-decode behavior, and total detection failure. Execution tests verify that detected encoding is exposed without mutating the request and that detection failure prevents downstream processing.

### Reopen when

Real-world inputs demonstrate that the fixed candidate set or ordering is insufficient, at which point any semantic detector or additional candidate should be introduced as an explicit new decision rather than an implicit heuristic.

---

## DD-11 — Automatic Chapter Renumbering

**Status: Frozen**

### Decision

Do not automatically renumber chapters.

### Reason

Preserve source structure and avoid implicit structural rewriting.

### Reopen when

A future requirement explicitly introduces structural normalization.

---

## DD-12 — Generic Semantic Chapter Inference

**Status: Frozen**

### Decision

Do not introduce generic semantic chapter inference as an implicit conversion heuristic.

### Reason

Prefer conservative parsing over speculative structural interpretation.

### Reopen when

An explicit product requirement establishes a defined semantic inference contract.

---

## DD-13 — Punctuation / Sentence-Length Paragraph Splitting

**Status: Frozen**

### Decision

Do not split paragraphs implicitly based on punctuation or sentence length.

### Reason

Paragraph boundaries should not be inferred from heuristic sentence characteristics.

### Reopen when

An explicit parsing requirement defines a reliable semantic contract.

---

## DD-14 — Global Arabic Numeral Conversion

**Status: Frozen**

### Decision

Do not perform global Arabic numeral conversion as an implicit transformation.

### Reason

Global character-level rewriting can alter legitimate source content.

### Reopen when

A future transformation policy explicitly defines the scope and semantics.

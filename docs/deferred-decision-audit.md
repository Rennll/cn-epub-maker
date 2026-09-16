# Deferred Decision Audit

## Status

This document is the decision register for architectural and behavioral questions that were intentionally left open, partially resolved, resolved, or frozen during V2 and V2.x work. It records decision status, current position, provenance, and conditions for revisiting a decision.

Detailed technical definitions belong to the canonical documents referenced by each decision. This document should not duplicate architecture documentation or serve as an implementation task list.

The audit currently covers DD-01 through DD-14. DD-15 has been moved to `future-directions.md` because it describes a future architecture direction rather than a current decision that needs tracking.

## Decision Status

| ID | Decision | Status | Primary dependency |
| --- | --- | --- | --- |
| DD-01 | Configuration Model | Resolved | Application architecture |
| DD-02 | JunkCleaner rule input | Resolved | Configuration Model |
| DD-03 | JunkCleaner default rules | Resolved | Configuration Model + DD-02 |
| DD-04 | Intermediate semantics | Resolved | Book model + provenance model |
| DD-05 | Paragraph mode vs. source-format profile | Resolved | Parser architecture |
| DD-06 | Normalize vs. Transformer responsibility | Resolved | Configuration Model + stage boundaries |
| DD-07 | Real-device typography completion criteria | Resolved | EPUB rendering behavior |
| DD-08 | EPUBCheck role | Resolved | Release/CI policy |
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

**Status: Resolved**

### Decision

JunkCleaner rules use a canonical structured `JunkRule` model and support a repeatable CLI shorthand. Structured configuration and CLI shorthand are parsed, normalized, validated, and canonicalized by a dedicated configuration rule layer before entering the resolved `ConversionRequest`.

Configuration-file rules and CLI rules are merged by append, preserving declared order. Invalid rule configuration, including invalid regular expressions, is rejected before execution. A valid rule that matches zero input is not an error.

The canonical rule model remains:

```text
JunkRule
├── target: "line" | "block"
├── matcher: "exact" | "contains" | "regex"
└── pattern: string
```

The structured configuration representation is JSON. CLI shorthand uses `TARGET:MATCHER:PATTERN`, with only the first two separators treated as syntax separators.

### Canonical

`docs/junk-rule-configuration.md`

### Related

`v2x-configuration-model.md`

### Evidence

The decision was established through the DD-02 architecture review and is now specified by the canonical rule configuration contract. Implementation and tests are tracked separately and do not reopen the architectural decision.

### Reopen when

A future requirement changes the canonical rule model, input forms, ordering semantics, validation contract, or configuration-source merge semantics.

---

## DD-03 — JunkCleaner Default Rules

**Status: Resolved**

### Decision

`JunkCleaner` has no built-in global default rules. The application-level `junk_rules` collection remains empty by default, preserving the existing no-rule runtime behavior.

No source-independent rule set was established with sufficiently strong evidence of non-content identification and sufficiently low risk of deleting legitimate正文 across the supported TXT population. Repository fixtures contain legitimate URLs, mixed CJK/Latin text, chapter/volume headings, and other material that broad semantic junk rules could incorrectly remove. External corpus review showed real source-specific contamination such as watermarks, fixed footers, and domain-bearing junk, but those patterns are not safe to promote to global defaults without source-specific scoping or stronger cross-source evidence.

The following are explicitly not global defaults: generic URL matching, generic `廣告`/`版權`/`作者`/`網站` keyword rules, generic contact/QQ matching, ISBN/publisher metadata matching, and currently observed source-specific domain/footer patterns.

DD-02 remains authoritative for application-default/config-file/CLI precedence, append ordering, validation, explicit empty collections, and Full Source Mode semantics. Source-specific rule profiles and detection/candidate-generation workflows remain outside DD-03.

### Canonical

`docs/dd-03-junkcleaner-default-rules.md`

### Evidence

The decision preserves the existing empty application default and is supported by repository fixtures plus external TXT corpus review. The evidence did not establish a sufficiently safe cross-source global rule set.

### Reopen when

Strong cross-source evidence establishes a low-false-positive global rule set, or the architecture explicitly introduces a source-profile mechanism that can safely scope rules to known source ecosystems.

---

## DD-04 — Intermediate Semantics

**Status: Resolved**

### Decision

Intermediate is a serialization and inspection artifact around the canonical in-memory `Book` model. It is not a second semantic model, runtime state, or independently rebuildable application artifact.

The current conversion pipeline treats `Book` as the canonical semantic representation between parsing and rendering. Intermediate serialization may expose that structured result for inspection, debugging, provenance, and future tooling, but the application does not require an Intermediate reader to continue a conversion.

Intermediate therefore does not currently promise arbitrary `Intermediate → Book` reconstruction, cross-version compatibility, migration, or a stable interchange-format contract.

### Canonical

`dd-04-intermediate-semantics.md`

### Related

`architecture-overview.md`

### Evidence

Current Intermediate serialization, `Book` model usage, and optional `--keep-intermediate` artifact generation.

### Reopen when

The project needs to rebuild a `Book` without the original source text, consume Intermediate from a separate process or tool, resume EPUB generation from an Intermediate artifact, or provide long-lived Intermediate files with compatibility guarantees. Such a requirement should be treated as a new architecture feature rather than inferred from the current serialization format.

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

**Status: Resolved**

### Question

What evidence is sufficient to declare EPUB typography and layout complete?

### Decision

A documented acceptance matrix and deterministic representative fixture are now in place. The generated baseline EPUB was validated structurally and with EPUBCheck, then tested as the same artifact in representative desktop and mobile/tablet reading environments.

The observed baseline was functionally acceptable across the matrix. Android ReadEra showed somewhat unusual layout for long continuous English/alphanumeric content, but no project-wide content, structure, overflow, or semantic defect was identified. Kindle Paperwhite 3 behavior after EPUB-to-AZW3 conversion was also normal for the tested cases. Both environments showed somewhat wider apparent right-side whitespace; this was treated as reader-dependent presentation variance rather than evidence of a generator defect.

No renderer or CSS tuning was justified by the observed evidence. The acceptance baseline therefore establishes the current renderer/CSS behavior as acceptable while explicitly retaining reader-dependent presentation differences outside the generator contract.

### Canonical

`docs/real-reader-acceptance-matrix.md`

`docs/v2x-typography-and-layout.md`

`tests/fixtures/real_reader_acceptance.txt`

`tests/test_real_reader_acceptance_fixture.py`

### Evidence

GitHub Actions generated and validated the representative EPUB artifact. The same artifact was manually inspected in Android ReadEra and on a Kindle Paperwhite 3 after EPUB-to-AZW3 conversion. The acceptance cases were reported as passing; the only noted variance was long continuous Latin/alphanumeric layout in ReadEra and wider apparent right-side whitespace in both environments.

### Reopen when

A reproducible generator defect, structural/content defect, or project-wide presentation problem is observed in the acceptance matrix, or a new target reader/environment becomes an explicit project requirement.

---

## DD-08 — EPUBCheck Role

**Status: Resolved**

### Decision

EPUBCheck is an external conformance validation layer. Normal `build` runs built-in EPUB validation only and does not require or invoke EPUBCheck. `validate` runs EPUBCheck when available and treats missing EPUBCheck as a warning by default. `validate --require-epubcheck` makes the external validator mandatory. CI and release use the strict policy, so missing EPUBCheck or EPUBCheck failures fail the gate.

### Canonical

`dd-08-epubcheck-validation-policy.md`

### Evidence

The policy is implemented through the validator's explicit required/optional mode and the CLI's `--require-epubcheck` option, with regression tests for missing and failing EPUBCheck states.

### Reopen when

The project changes the boundary between local validation and release/CI conformance requirements, or adopts a different external conformance tool.

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

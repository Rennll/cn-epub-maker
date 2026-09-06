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
| DD-09 | Output filename sanitization and overwrite policy | Open | Destination/CLI policy |
| DD-10 | Encoding auto-detection guarantee and positioning | Partially resolved | Input policy + runtime behavior |
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

**Status: Open**

### Question

How should destination paths, generated filenames, collisions, and overwrites be handled?

### Decision needed

- filename derivation;
- filesystem character sanitization;
- path traversal handling;
- overwrite behavior;
- parent-directory creation;
- collision reporting.

### Architectural boundary

Destination and overwrite behavior are application policy and should not be implicit renderer side effects.

### Resolve when

CLI/API behavior and the destination contract are explicit and consistent.

---

## DD-10 — Encoding Auto-Detection Guarantee and Positioning

**Status: Partially resolved**

### Question

What guarantee should automatic encoding detection provide, and where does it belong in the conversion boundary?

### Current decision

Encoding detection remains input/runtime behavior rather than part of the serialized conversion request.

### Remaining question

What confidence/failure guarantees should be exposed to users, and how should detection failure or ambiguity be reported?

### Canonical

`novel_epub/normalize.py`

### Related

`v2x-configuration-model.md`

### Resolve when

Detection behavior, failure semantics, and user-visible guarantees are explicitly defined.

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

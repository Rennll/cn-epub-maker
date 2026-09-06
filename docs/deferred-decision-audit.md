# Deferred Decision Audit

## Status

This document records the architectural decisions that were intentionally deferred during the V2 and V2.x design work. It is a decision-tracking document, not a list of implementation tasks.

The purpose is to make three things explicit for each decision:

1. what remains undecided,
2. what architectural work has already constrained the decision, and
3. what evidence or implementation work is required before the decision can be considered complete.

The audit covers DD-01 through DD-15.

## Decision Status

| ID | Decision | Status | Primary dependency |
| --- | --- | --- | --- |
| DD-01 | Configuration Model | Resolved | Application architecture |
| DD-02 | JunkCleaner rule input | Open, ready to decide | Configuration Model |
| DD-03 | JunkCleaner default rules | Open, ready to decide | Configuration Model + DD-02 |
| DD-04 | Intermediate semantics | Partially resolved | Configuration Model + provenance model |
| DD-05 | Paragraph mode vs. source-format profile | Deferred | Parser architecture |
| DD-06 | Normalize vs. Transformer responsibility | Resolved | Configuration Model + stage boundaries |
| DD-07 | Real-device typography completion criteria | Open | EPUB rendering behavior |
| DD-08 | EPUBCheck role | Open | Release/CI policy |
| DD-09 | Output filename sanitization and overwrite policy | Open | Destination/CLI policy |
| DD-10 | Encoding auto-detection guarantee and positioning | Partially resolved | Input policy + runtime behavior |
| DD-11 | Automatic chapter renumbering | Frozen | Structural preservation |
| DD-12 | Generic semantic chapter inference | Frozen | Parser conservatism |
| DD-13 | Punctuation/sentence-length paragraph splitting | Frozen | Paragraph semantics |
| DD-14 | Global Arabic numeral conversion | Frozen | Transformation conservatism |
| DD-15 | Intermediate → Book → EPUB rebuilding | Deferred future architecture | Intermediate evolution |

## How to Read This Audit

A decision marked **Resolved** has a stable architectural answer and should not be reopened merely because implementation remains incomplete.

A decision marked **Partially resolved** has a stable architectural direction, but one or more operational or implementation-level questions remain.

A decision marked **Open, ready to decide** has enough architectural foundation to make the remaining product or behavior decision without changing the Configuration Model.

A decision marked **Deferred** is intentionally left for later because the required evidence or architecture is not yet mature enough.

A decision marked **Frozen** is an explicit non-goal or invariant. It should not be reintroduced through convenience heuristics or implementation shortcuts without a deliberate architectural revision.

---

## DD-01 — Configuration Model

**Status: Resolved**

### Decision

The application-level configuration model is represented by a `ConversionRequest` containing source information, book metadata, destination information, and a `ConversionPolicy`.

The conceptual model is:

```text
ConversionRequest
├── source
├── book_metadata: BookMetadata
├── destination
└── policy: ConversionPolicy
    ├── encoding
    ├── parser: ParserPolicy
    │   └── paragraph_mode
    ├── transformations: TransformationPolicy
    │   ├── opencc: OpenCCConfig
    │   ├── punctuation_enabled
    │   └── junk_cleaner: JunkCleanerConfig
    │       └── rules
    └── full_source
```

`ConversionRequest` describes one requested conversion operation. It is not a `Book`, not an execution context, and not a pipeline implementation object.

### Architectural consequences

The CLI is an adapter into the application configuration model. `argparse.Namespace` is not the application configuration model.

Configuration resolution is a separate boundary:

```text
CLI / config file / API
        ↓
configuration resolution
        ↓
ConversionRequest
        ↓
execution
```

The resolver owns application defaults, precedence, cross-field semantics, and configuration-level validation. It does not read source files, detect encodings, instantiate transformers, compile regular expressions, parse books, or render EPUBs.

Component-specific validation remains owned by the component. Runtime failures remain runtime concerns.

### Completion criteria

DD-01 is considered complete when new frontends can construct the same application-level request without depending on CLI syntax, and when execution stages consume only the policy they require.

---

## DD-02 — JunkCleaner Rule Input

**Status: Open, ready to decide**

### Question

How should users define and provide `JunkRule` entries?

### Architectural foundation

The Configuration Model already provides the correct ownership boundary:

```text
ConversionRequest
└── policy
    └── transformations
        └── junk_cleaner
            └── rules
```

The rule configuration is component-local configuration. It should not become a generic pipeline configuration mechanism.

The existing JunkCleaner design defines the semantic schema as:

```text
JunkRule
├── target
├── matcher
└── pattern
```

The intended target values are `line` and `block`. The intended matcher values are `exact`, `contains`, and `regex`.

### Current semantic contract

`line` targets one normalized source line and cannot cross a newline boundary.

`block` targets one or more consecutive non-blank lines. Blank lines are boundaries between blocks.

`exact` matches the complete target against the pattern.

`contains` matches when the pattern occurs within the target.

`regex` uses regular-expression search semantics against the current target.

JunkCleaner is remove-only. A matching rule removes the entire target; it does not replace only the matching substring.

Rules are applied in user-defined order. Each rule operates on the result of the previous rule.

An invalid regular expression is a rule-level configuration error that may be reported as a warning and skipped without aborting the entire conversion, according to the existing V2 transformation contract.

### Remaining decision

The public input mechanism still needs to be chosen. The architectural preference is to define the typed rule schema first and keep the external representation replaceable. A future configuration file format should map into the same `JunkCleanerConfig` rather than define a second semantic model.

The decision should explicitly cover:

- programmatic/API representation,
- external configuration representation, if any,
- whether CLI-only shorthand is supported,
- rule ordering guarantees,
- malformed rule behavior,
- invalid regex behavior,
- audit representation of rule matches and removals.

### Completion criteria

DD-02 is complete when the public rule schema and loading path are documented, implemented, and covered by unit and integration tests, including `line`, `block`, `exact`, `contains`, `regex`, ordering, no-match behavior, and invalid regex behavior.

---

## DD-03 — JunkCleaner Default Rules

**Status: Open, ready to decide**

### Question

Should JunkCleaner have built-in default rules, and if so, which rules are safe enough to enable by default?

### Architectural foundation

The Configuration Model establishes the correct authority boundary: application defaults are resolved by the Configuration Resolver, while JunkCleaner owns the semantics of individual rules.

This means default rules should not be hidden inside the parser or renderer. They are transformation policy defaults.

Issue #17 explicitly identifies this as an unresolved design question and requires conservative behavior so that default cleaning does not remove正文 content without adequate specification and tests.

### Decision principle

A default rule must be justified by strong evidence that it identifies non-content material rather than merely unusual prose.

A rule that can plausibly match legitimate narrative text should not be enabled globally merely because it is useful for one source website or one author's formatting style.

### Remaining decision

The project must decide:

- whether the default rule set is empty, conservative, or source-profile-specific,
- whether defaults can be disabled as a group,
- whether user rules replace or extend defaults,
- whether source-specific defaults belong in a future source-format profile instead,
- how default-rule provenance is represented in transformation audit data.

### Completion criteria

DD-03 is complete when the default set, precedence with user-defined rules, safety rationale, and test coverage are documented. A default rule should not be introduced without regression coverage for both intended junk and plausible正文 false positives.

---

## DD-04 — Intermediate Semantics

**Status: Partially resolved**

### Question

What is the authoritative semantic role of the Intermediate representation?

### Current direction

The Configuration Model clarifies an important distinction:

```text
ConversionRequest   = requested policy
Runtime Data        = data while conversion executes
Book                = parsed domain result
Intermediate        = serialized Book + provenance/audit metadata
EPUB                = final rendered result
```

Intermediate is not a pipeline stage and is not a copy of the raw source text.

The current implementation serializes the `Book` and transformation audit information. It does not reconstruct the `Book` from Intermediate yet.

### Decision

For the current V2.x architecture, Intermediate remains a serialization and inspection boundary around the `Book` plus transformation provenance. It should preserve enough information to inspect what conversion produced and what transformations were applied.

The exact question of whether Intermediate must become a canonical, independently rebuildable artifact is intentionally deferred to DD-15.

### Remaining questions

The project still needs to determine:

- which metadata is mandatory for reproducibility,
- whether request configuration or only effective transformation provenance belongs in Intermediate,
- versioning and compatibility rules for Intermediate,
- whether an Intermediate file can become a stable input to a later conversion stage,
- how schema evolution is handled.

### Completion criteria

DD-04 is complete for the current V2.x scope when the required serialized fields and provenance semantics are documented. It is not necessary to solve full Intermediate round-tripping before V2.x transformation work proceeds.

---

## DD-05 — Paragraph Mode vs. Source-Format Profile

**Status: Deferred**

### Question

Should `paragraph_mode` remain a direct parser policy, or should it eventually be part of a higher-level source-format profile?

### Current decision

`paragraph_mode` remains part of `ParserPolicy`:

```text
ConversionPolicy
└── parser
    └── paragraph_mode
```

The supported semantic modes are currently `wrapped` and `line`.

This is preferable to introducing a broader `SourceFormatConfig` before there is a concrete set of source-format policies that belong together.

### Why it remains deferred

The distinction may become useful if the project accumulates multiple source-specific behaviors such as parser grammar, paragraph conventions, encoding defaults, and known cleanup rules. At present, combining them would create an abstraction before the requirements justify it.

### Completion criteria

Revisit this decision only when multiple source-specific behaviors need to be selected as a coherent profile. Do not create `SourceFormatConfig` merely to group one parser option.

---

## DD-06 — Normalize vs. Transformer Responsibility

**Status: Resolved**

### Decision

Normalization remains a system-defined input interpretation stage. It is not part of user-configurable transformation policy.

The current normalization responsibilities include:

- canonicalizing line endings,
- removing a leading U+3000 from a normalized line,
- preserving the remaining source content.

Transformers operate after normalization and are policy-driven. They include OpenCC, punctuation transformation, and JunkCleaner.

The resulting boundary is:

```text
Decode
  ↓
Normalize
  ↓
Transform
  ↓
Parse
```

### Architectural rule

Not everything that changes output is configuration. A behavior belongs in configuration when it represents user-selectable policy. An inherent part of the input grammar or system interpretation remains outside configuration.

### Completion criteria

DD-06 is complete when new normalization behavior is evaluated against this boundary rather than being added to the transformation pipeline simply because it changes text.

---

## DD-07 — Real-Device Typography Completion Criteria

**Status: Open**

### Question

What evidence is sufficient to declare EPUB typography and layout complete?

### Scope

This decision is independent of the Configuration Model. Configuration can expose typography policy in the future, but the completion criterion itself depends on rendered EPUB behavior across real reading environments.

### Required evidence

The project should define a repeatable acceptance set covering at least:

- paragraph spacing,
- line spacing,
- heading hierarchy,
- margins and page geometry,
- long chapter behavior,
- CJK text rendering,
- punctuation and line breaking,
- metadata presentation,
- cover rendering,
- navigation and table of contents,
- common EPUB readers or representative device/software combinations.

### Completion criteria

DD-07 is complete when the project has a documented acceptance matrix and can distinguish implementation defects from reader-specific rendering differences.

Typography should not be declared complete solely because an EPUB validates structurally or renders acceptably in one reader.

---

## DD-08 — EPUBCheck Role

**Status: Open**

### Question

Is EPUBCheck an optional developer tool, or a required release/CI correctness gate?

### Current architecture

The project already has built-in EPUB structural validation and supports optional EPUBCheck integration.

This decision is independent of the Configuration Model. Configuration may eventually control whether validation is requested, but the architectural question is about release policy and correctness guarantees.

### Decision to make

The project should distinguish at least three levels:

1. built-in validation required for normal conversion,
2. EPUBCheck available for deeper conformance verification,
3. EPUBCheck required before release or in CI.

### Completion criteria

DD-08 is complete when the project explicitly states which checks are mandatory for local conversion, which are recommended for development, and which are required for release.

---

## DD-09 — Output Filename Sanitization and Overwrite Policy

**Status: Open**

### Question

How should destination paths, generated filenames, collisions, and overwrites be handled?

### Architectural foundation

The Configuration Model places the destination in `ConversionRequest`, which is sufficient to represent the requested destination. It does not define filesystem safety policy by itself.

### Remaining questions

The project should decide:

- whether an output filename is explicitly supplied or derived from metadata,
- how unsafe filesystem characters are handled,
- whether path traversal is rejected,
- whether existing files are overwritten by default,
- whether overwrite requires an explicit option,
- whether parent directories are created automatically,
- how output collisions are reported.

### Architectural boundary

Filename derivation and overwrite behavior are destination/application policy. They should not be implemented inside the renderer as implicit side effects.

### Completion criteria

DD-09 is complete when the destination contract is explicit and CLI/API behavior is consistent.

---

## DD-10 — Encoding Auto-Detection Guarantee and Positioning

**Status: Partially resolved**

### Decision

Encoding selection is an input policy. The request may specify an explicit encoding or `auto`.

The actual encoding detected at runtime is not configuration. It is runtime/provenance information.

The conceptual flow is:

```text
ConversionRequest
└── policy
    └── encoding = explicit value | auto

runtime
└── detected_encoding
```

The current supported encodings are UTF-8 with BOM, UTF-8, GB18030, GBK, and Big5, with BOM-aware and trial-based detection behavior.

### Remaining question

The unresolved part is the guarantee provided by `auto` detection. The project must decide whether detection is best-effort, deterministic for the supported encoding set, or required to fail when confidence is insufficient.

The request should not be mutated to replace `auto` with the detected encoding. If reproducibility requires recording the actual encoding, it belongs in runtime/provenance or Intermediate metadata.

### Completion criteria

DD-10 is complete when auto-detection failure/ambiguity behavior is documented and tested, including the relationship between requested encoding and actual detected encoding.

---

## DD-11 — Automatic Chapter Renumbering

**Status: Frozen**

### Decision

The parser must not automatically renumber chapters.

Sequence discovery follows source order. Missing numbers, duplicate numbers, or irregular numbering may produce validation warnings, but the system must not silently rewrite the source structure.

### Rationale

Renumbering changes source semantics and makes the generated Book differ from the user's source without explicit transformation policy.

### Consequence

If renumbering is ever required, it must be introduced as an explicit transformation or a separately defined structural operation. It must not appear as a parser convenience feature.

---

## DD-12 — Generic Semantic Chapter Inference

**Status: Frozen**

### Decision

The parser must not infer chapters from generic semantic cues such as arbitrary heading-like text, sentence content, or contextual guesses.

Chapter recognition remains based on explicit parser grammar and supported structural patterns.

### Rationale

Generic semantic inference creates false positives and makes source preservation unpredictable. The V1 and V2 architecture deliberately prefers conservative recognition and warnings over guessing.

### Consequence

Adding a new structural pattern requires an explicit grammar decision and test coverage rather than a broad heuristic.

---

## DD-13 — Punctuation or Sentence-Length Paragraph Splitting

**Status: Frozen**

### Decision

Punctuation density, sentence length, or similar linguistic heuristics must not be used to infer paragraph boundaries.

Paragraph boundaries are determined by source structure and explicit parser policy.

### Rationale

Sentence-level heuristics are language-dependent and can change the semantic structure of a source in ways that are difficult to predict or audit.

The current parser therefore treats blank-line boundaries and the explicit `paragraph_mode` as authoritative structural signals.

### Consequence

If future linguistic segmentation is introduced, it must be an explicit, separately scoped feature rather than a hidden parser heuristic.

---

## DD-14 — Global Arabic Numeral Conversion

**Status: Frozen**

### Decision

The system must not perform global Arabic numeral conversion as an implicit transformation.

For example, changing all Arabic digits to another numeral representation is outside the default structural conversion pipeline.

### Rationale

Numerals may represent chapter numbers, dates, measurements, identifiers, quantities, names, or literal source content. A global conversion rule cannot safely infer the intended semantic role.

### Consequence

Numeral conversion, if ever required, must be an explicit and narrowly defined transformation with a documented scope.

---

## DD-15 — Intermediate → Book → EPUB Rebuilding

**Status: Deferred future architecture**

### Question

Should Intermediate become a canonical, rebuildable artifact that can independently feed the Book and EPUB stages?

### Current architecture

The current V2.x path is:

```text
Source
  ↓
Normalize
  ↓
Transform
  ↓
Parser
  ↓
Book
  ├── Intermediate
  └── EPUB
```

A future architecture may support:

```text
Intermediate
  ↓
Book
  ↓
EPUB
```

### Relationship to DD-04

DD-04 establishes the current semantic boundary of Intermediate. DD-15 asks whether that boundary should become a first-class reconstruction interface.

The Configuration Model does not solve this decision. It only makes the distinction between request policy, runtime state, Book, and Intermediate clearer.

### Why it is deferred

Rebuildability affects schema versioning, compatibility, provenance, asset handling, validation, and the long-term contract of the Intermediate format. Solving it prematurely would constrain the current transformation work without enough evidence.

### Completion criteria

DD-15 should be revisited when there is a concrete use case for:

- editing or inspecting Intermediate and rebuilding EPUB,
- resuming conversion without reparsing source text,
- deterministic regeneration from serialized Book data,
- tooling that consumes Intermediate as a stable interchange format.

The decision should then define schema versioning, compatibility guarantees, asset representation, provenance requirements, and rebuild validation.

---

## Dependency Map

The decisions do not form one linear sequence. Their dependencies are better represented as a small set of architectural groups.

```text
Configuration Model
        │
        ├── DD-02 JunkCleaner rule input
        │       │
        │       └── DD-03 JunkCleaner defaults
        │
        ├── DD-06 Normalize vs Transformer
        │
        ├── DD-10 Encoding policy
        │
        ├── DD-04 Intermediate semantics
        │       │
        │       └── DD-15 Intermediate rebuildability
        │
        └── DD-05 Paragraph mode vs source profile

Independent runtime / release decisions
        ├── DD-07 Typography completion
        ├── DD-08 EPUBCheck role
        └── DD-09 Output destination policy

Frozen structural invariants
        ├── DD-11 No automatic chapter renumbering
        ├── DD-12 No generic semantic chapter inference
        ├── DD-13 No heuristic paragraph splitting
        └── DD-14 No implicit global numeral conversion
```

## Recommended Decision Order

The recommended next sequence is:

1. **DD-02 — JunkCleaner rule input**
2. **DD-03 — JunkCleaner default rules**
3. **DD-04 — Intermediate semantics**
4. **DD-10 — Encoding auto-detection guarantee**
5. **DD-05 — Paragraph mode vs. source-format profile**, only if new source-format requirements emerge
6. **DD-09 — Output filename and overwrite policy**
7. **DD-08 — EPUBCheck release/CI role**
8. **DD-07 — Real-device typography completion criteria**
9. **DD-15 — Intermediate rebuildability**, when a concrete use case justifies it

DD-11 through DD-14 should remain frozen unless the project explicitly changes its source-preservation philosophy.

## Architectural Principle

The purpose of this audit is not to eliminate every future design question. It is to make the boundary between solved architecture, implementation policy, empirical validation, and deliberate non-goals explicit.

The current V2.x architecture therefore follows four rules:

1. Resolve architectural boundaries before adding implementation options.
2. Keep user-selectable policy in the Configuration Model and inherent system interpretation outside it.
3. Prefer explicit behavior and warnings over semantic guessing.
4. Do not turn a deferred question into an accidental behavior through implementation convenience.

A deferred decision is not permission for code to choose implicitly. Until a decision is resolved, the implementation should follow the safest behavior already established by the current architecture.

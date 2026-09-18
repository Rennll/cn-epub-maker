# Architecture Contract

Status: Contract baseline

This document records the architectural boundaries and invariants intentionally protected by the current implementation. It complements the high-level architecture overview and stage-specific contracts.

## 1. Canonical build pipeline

The normal build is conceptually:

```text
Raw TXT
  ↓
Representation Normalization
  ↓
Content Transformations
  ↓
Physical Document
  ↓
Document Analysis
  ↓
Document Formatting Model
  ↓
Parser / Semantic Inference
  ↓
Book
  ↓
Book Validation
  ↓
Renderer
  ↓
EPUB
  ↓
EPUB Validation
```

Optional Intermediate serialization observes the canonical `Book` result and transformation audit; it is not an additional execution stage.

Inspection is a separate authoring workflow:

```text
Raw TXT
  ↓
Inspection / Detection
  ↓
Detection Groups
  ↓
Suggested JunkRules
  ↓
Rule Preview
  ↓
User Decision
  ↓
JSON Configuration
  ↓
Normal Build
```

Normal build MUST NOT implicitly invoke inspection.

## 2. Physical and semantic boundaries

`PhysicalDocument` represents observable ordered source structure after normalization and content transformations. `Book`, `Chapter`, `Paragraph`, and related objects represent semantic interpretation.

- Document Analysis observes the Physical Document and produces evidence.
- Parser consumes the Physical Document and analysis evidence to infer semantic structure.
- Document Analysis MUST NOT create semantic Chapter, Volume, Paragraph, or similar structures.
- Parser MUST NOT replace the Physical Document with a separately reconstructed representation.
- Renderer MUST consume semantic `Book` data rather than re-parse raw source text.
- A Physical Block MUST NOT be assumed to equal one semantic Paragraph.
- A semantic Paragraph MAY contain multiple Physical Lines.

Inspection follows the same physical-domain principle: detection targets physical lines and blocks, not semantic `Book` objects.

Detailed physical-document rules remain in `physical-document-and-formatting-contract.md`.

## 3. Inspection boundary

Inspection is observation and rule authoring, not automatic removal.

Detection MUST be read-only with respect to the source, observe physical lines and blocks, produce traceable evidence, avoid semantic structure inference, and avoid executing transformations.

Detection MUST NOT modify `PhysicalDocument`, execute `JunkCleaner`, delete source content, or silently turn a detection result into an executable rule.

A SuggestedRule MUST use the canonical `JunkRule` model. Detection MUST NOT introduce a second executable rule language.

The user acceptance/edit/skip boundary is where a suggestion becomes an intentional configuration choice.

## 4. JunkRule matching contract

`JunkRule` is the canonical executable contract shared by inspection and normal transformation:

```text
JunkRule
├── target: line | block
├── matcher: exact | contains | regex
└── pattern: string
```

Rule configuration owns parsing, normalization, and validation. JunkCleaner owns execution.

Inspection Rule Preview MUST use the same matching semantics as JunkCleaner. Detection MUST NOT maintain a separate interpretation of `exact`, `contains`, or `regex`.

A valid rule with zero matches is not a configuration error. An invalid rule is a configuration error and MUST NOT silently become a successful conversion.

The detailed rule configuration contract is defined in `junk-rule-configuration.md`.

## 5. Transformation ordering

The current normal-build transformation order is a contract:

```text
JunkCleaner
    ↓
OpenCC
    ↓
Punctuation Conversion
```

Inspection-generated JunkRules therefore target the source/physical text domain before later content transformations.

Configuration resolution MUST preserve declared JunkRule order within the JunkCleaner stage. It MUST NOT sort or deduplicate rules implicitly.

The transformation pipeline is intentionally simple and sequential. A future implementation may change the mechanism only if observable ordering semantics remain unchanged and this contract and its tests are updated.

Full Source Mode MAY suppress content transformations, but it MUST NOT bypass Document Analysis or Parser input contracts.

## 6. Configuration and execution boundary

Configuration resolution converts external inputs into an immutable `ConversionRequest`.

`ConversionRequest` describes requested conversion behavior. It MUST NOT contain runtime facts such as `Book`, detected/actual encoding, transformation audit, runtime warnings, instantiated transformers, or execution state.

Runtime results belong to `ExecutionResult` and related runtime/audit structures.

The configuration resolver MUST resolve defaults, precedence, validation, and policy composition. It MUST NOT perform conversion, rendering, or EPUB validation.

The application execution layer orchestrates conversion after a resolved `ConversionRequest` exists.

## 7. Intermediate boundary

Intermediate is an optional serialized inspection/debug artifact around the canonical `Book` result.

It MAY contain transformation audit/provenance needed to understand a build result.

It MUST NOT become a second semantic domain model, a replacement for `PhysicalDocument`, an implicit execution plan, a required reverse-reconstruction API for `Book`, or a place to store `ConversionRequest` as runtime state.

Changes to Intermediate semantics should be treated as artifact/schema changes, not as a way to bypass Parser or configuration boundaries.

## 8. Parser and renderer boundary

Parser owns semantic inference. Renderer owns publication representation.

Renderer MUST NOT infer chapters, paragraphs, or other source semantics from raw whitespace or source text. Renderer MUST NOT depend on Detection, `JunkRule` configuration, or ConfigurationResolver.

The renderer receives the canonical semantic model and produces publication-oriented output. EPUB packaging remains an output concern separate from source parsing and transformation.

## 9. Validation boundaries

Validation has independent layers:

1. Book/model validation checks the semantic `Book`.
2. EPUB structural validation checks the generated package.
3. Optional EPUBCheck provides additional external standards validation.

These layers MUST remain independently callable and MUST NOT be collapsed into a single validator that assumes one representation can validate all others.

Validation checks results; it does not define upstream semantics.

## 10. Architecture invariants

1. Detection never mutates source content.
2. Detection never executes `JunkCleaner`.
3. SuggestedRule uses canonical `JunkRule`.
4. Inspection Rule Preview and JunkCleaner share matching semantics.
5. PhysicalDocument does not depend on semantic Parser output.
6. Document Analysis does not perform semantic Chapter / Paragraph inference.
7. Parser and Document Analysis observe the same post-transformation Physical Document.
8. Generated inspection config is ordinary build configuration.
9. Normal build does not implicitly invoke inspection.
10. `ConversionRequest` contains configuration intent, not runtime state.
11. Configuration resolution does not execute conversion.
12. JunkCleaner, OpenCC, and Punctuation execute in the declared order.
13. Intermediate does not become a second domain model or required reverse-conversion format.
14. Renderer consumes `Book` rather than raw source semantics.
15. Book validation and EPUB validation remain separate boundaries.
16. Full Source Mode does not bypass Document Analysis or Parser input contracts.
17. Configuration rule order is preserved through resolution and execution.
18. Configuration history and inspection provenance are not implicitly stored in formal JunkRule configuration.

## 11. Change policy

A change that crosses one of these boundaries should first update the relevant contract and tests.

A change that only refactors an internal implementation while preserving the observable boundary does not require architectural redesign.

When a new requirement appears, prefer a narrowly scoped contract over a generic abstraction without a concrete use case.

The current architecture is intentionally conservative: it protects physical/source semantics, user-authorized transformation, configuration/execution separation, and renderer/validation boundaries without requiring a universal document model or pipeline framework.

## 12. Related contracts

- `architecture-overview.md` — high-level architecture map.
- `physical-document-and-formatting-contract.md` — physical structure, formatting evidence, and parser boundary.
- `junk-rule-configuration.md` — canonical JunkRule configuration and validation.
- `junk-detection-contract.md` — inspection, detection evidence, suggestion, preview, and user decision flow.
- `v2x-configuration-model.md` — application configuration model and precedence.

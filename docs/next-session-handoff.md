# Next Session Handoff

## Current Context

The repository is now past the main V2.x architecture refactor and the inspection hardening sequence.

The current main baseline is:

`9a40524b0ec93baeb94f678efc080d25cfd0bf75`

The recent completed work includes:

- #60 Junk Detection baseline
- #67 parser refactor
- #68 renderer / EPUB packaging separation
- #69 validation split
- #75 JunkCleaner blank-line cleanup
- #81 candidate qualification / false-positive protection
- #82 inspection output lifecycle / failure safety
- #83 Rule Preview ↔ JunkCleaner integration invariant
- #84 deterministic multi-variable pattern abstraction
- #94 / #95 inspection CLI → generated JSON config → normal build E2E coverage
- #96 repository-wide architecture contract
- #97 architecture boundary regression tests

The current architecture should be treated as an established baseline rather than an invitation to start another broad refactor.

The public inspection workflow is now:

```text
novel-epub inspect source.txt --output junk-config.json
    ↓
Detection
    ↓
Candidate qualification
    ↓
Suggested JunkRule
    ↓
Rule Preview
    ↓
User accept / edit / skip
    ↓
JSON JunkRule config
    ↓
normal novel-epub build --config junk-config.json
    ↓
JunkCleaner
```

Normal build remains separate:

```text
Raw TXT
  ↓
Representation Normalization
  ↓
JunkCleaner → OpenCC → Punctuation
  ↓
PhysicalDocument
  ↓
Document Analysis / Formatting Model
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

Inspection is read-only and does not implicitly run during normal builds.

## GitHub Issue State

GitHub Issues remain the authoritative work queue. This document must not become a second priority tracker.

At the time of this handoff, the remaining open issues are:

### #71 — Architecture: second-stage refactoring roadmap

This is a tracking issue, not an implementation task.

Its historical sequence is now substantially complete. In particular, #81, #82, #83, #84, and #73 are closed. Do not treat the old sequence in #71 as an active dependency chain.

If #71 is revisited, update its body to reflect the current state rather than reopening completed architecture work.

### #70 — Preserve source-line provenance through transformations

This remains intentionally deferred.

The native XHTML/EPUB 3 work in #73 is now complete, so the original dependency condition has been reached. However, #70 should still not be implemented merely because its dependency is satisfied.

Only start #70 when there is a concrete debugging, audit, reporting, or user-facing provenance requirement that justifies adding provenance to the transformation pipeline.

Do not introduce source provenance preemptively.

## Current Work Queue Rules

1. Inspect the current open GitHub Issues before choosing work.
2. Treat GitHub Issue state and issue bodies as authoritative.
3. Do not treat historical order numbers in old issue text as the current priority system.
4. Do not work on a deferred issue unless its reopen condition is actually satisfied.
5. Read the issue body, direct dependencies, and referenced canonical docs before implementation.
6. Keep dependency metadata in issues accurate; do not recreate dependency state in this document.
7. After implementation, run focused tests and relevant end-to-end regression tests before closing the issue.
8. Update canonical documentation when a stable contract or architectural decision changes.
9. Do not create a new architecture issue merely to continue the completed V2.x refactor.
10. Prefer a concrete product/correctness requirement over speculative infrastructure.

## Established Architecture Boundaries

The following boundaries are now protected by `docs/architecture-contract.md` and regression tests:

1. Physical source representation and semantic `Book` representation remain separate.
2. Detection observes physical lines/blocks and does not depend on semantic Parser structures.
3. Detection never mutates source content or executes `JunkCleaner`.
4. SuggestedRule always uses the canonical `JunkRule` model.
5. Rule Preview and JunkCleaner share the same matching semantics.
6. Inspection output is ordinary build configuration, not inspection history.
7. Normal build does not implicitly invoke inspection.
8. Configuration resolution produces an immutable `ConversionRequest` and does not execute conversion.
9. Transformation order remains `JunkCleaner → OpenCC → Punctuation`.
10. Intermediate remains an artifact around the canonical `Book`, not a second semantic model.
11. Parser owns semantic inference; Renderer consumes `Book` rather than reparsing source text.
12. Book validation and EPUB validation remain separate concerns.
13. Full Source Mode does not bypass the Document Analysis / Parser input contract.
14. Configuration rule ordering is preserved through resolution and execution.

When a future change crosses one of these boundaries, update the relevant contract and tests first.

## Inspection / Junk Detection Notes

The inspection subsystem is now considered functionally integrated, not merely experimental.

Important current contracts:

- Detection is observation, not classification or removal.
- Candidate qualification is intentionally conservative.
- Numeric/structured patterns must not become destructive SuggestedRules from repetition alone.
- Pattern abstraction remains deterministic and narrow.
- Multi-variable patterns are supported without turning the detector into a general parser.
- Preview is read-only and uses canonical JunkRule matching semantics.
- Accepted inspection output contains only final JunkRules.
- Detection evidence, preview data, acceptance history, and provenance are not stored in the formal JunkRule config.
- Failed inspection runs must not leave a misleading final output file.
- Existing output files remain protected from overwrite.

The relevant canonical documents are:

- `docs/architecture-contract.md`
- `docs/junk-detection-contract.md`
- `docs/junk-rule-configuration.md`
- `docs/physical-document-and-formatting-contract.md`

## Deferred Decisions

Before reopening an architectural question, check:

`docs/deferred-decision-audit.md`

Current frozen decisions include:

- no automatic chapter renumbering;
- no implicit generic semantic chapter inference;
- no punctuation/sentence-length paragraph splitting;
- no global Arabic numeral conversion.

These should not be reintroduced as convenience heuristics.

## Next Session Guidance

At the beginning of the next session:

1. Inspect the live open GitHub Issues again; do not rely on this file as a static roadmap.
2. Confirm whether #70 has acquired a concrete provenance/reporting requirement.
3. If not, do not implement #70 solely because it is open.
4. If a new product or correctness issue exists, create or work from that issue instead of extending the old architecture roadmap.
5. Preserve the current physical/semantic, inspection/transform, configuration/execution, parser/renderer, and validation boundaries.
6. For EPUB-generation changes, trace the full path from `Book` through rendering, packaging, and validation before changing architecture.
7. Prefer focused regression tests and realistic fixtures over broad refactors.

## Handoff Notes

Use this section only for session-specific context that cannot be recovered from the repository or GitHub Issues.

Current session completed:

- architecture contract formalized;
- architecture boundary regression tests added;
- inspection CLI-to-build workflow covered end-to-end;
- no known architecture defect requiring another refactor.

Current recommendation for the next session:

Do not start another architecture cleanup by default. First inspect the live issue queue and only proceed when there is a concrete requirement or correctness gap to address.

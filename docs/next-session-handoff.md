# Next Session Handoff

## Next Session

The V2.x architecture refactor is complete. The next phase is to validate the existing contracts in real EPUB output and close the remaining operational decisions.

### Immediate Queue

1. **#27 — Validate generated EPUB in real reading environments (P0)**
   - Build a representative acceptance matrix covering CJK text, headings, paragraph boundaries, scene breaks, long chapters, typography/layout, and navigation.
   - Test in at least two representative reading environments.
   - Separate project guarantees from reader-specific variance.
   - Turn high-value regressions into automated tests or documented manual acceptance checks.

2. **#28 — Define and enforce EPUBCheck validation policy (P0)**
   - Define the roles of built-in validation and EPUBCheck.
   - Specify discovery, exit-code handling, missing-tool behavior, and CI/release gating.
   - Add the corresponding automated tests and documentation.

After the two P0 items are established, continue with the P1 queue as dependencies allow.

## P1 Follow-up

- **#17 — Define JunkCleaner default rules and user-facing rule configuration**
  - P1, but not part of the immediate queue.
  - Resolve DD-02 (rule input/configuration) and DD-03 (default rules) before implementation.
  - Preserve the existing safety requirement: default behavior must not risk deleting正文 without explicit specification and test coverage.
- **DD-09 — Output filename sanitization and overwrite policy**
  - Define destination, filename derivation/sanitization, overwrite, parent-directory, path-traversal, and collision behavior.
- **DD-10 — Encoding auto-detection guarantee and positioning**
  - Define confidence/failure behavior and user-visible reporting; keep encoding detection as input/runtime behavior rather than serialized request configuration.
- **Parser edge-case contract audit**
  - Audit remaining parser behavior and convert stable, high-value guarantees into regression tests.

## Later / P2

- DD-04 / intermediate schema and rebuild semantics.
- Packaging and release engineering hardening.
- Configuration-file frontend only after JunkCleaner rule schema and configuration semantics are stable.

## Decision Register

Do not duplicate the decision register here. Open and partially resolved architectural/behavioral decisions are tracked in `docs/deferred-decision-audit.md`. Resolve decisions there first, then reflect implementation work in issues and canonical documentation.

## Non-Goals

Do not reopen the following without a concrete new requirement or evidence:

- Generic LayoutEngine abstraction.
- Generic Theme abstraction.
- Automatic semantic chapter inference.
- Automatic chapter renumbering.
- Punctuation/sentence-length paragraph splitting.
- Global Arabic numeral conversion.
- Renderer-side text intelligence.

## Working Notes

- Keep the handoff focused on the next executable work, not as a second long-term roadmap.
- GitHub issues are the authoritative work queue; this document records what the next session should pick up first.
- Preserve the current architecture boundaries and avoid speculative abstraction while validation evidence is still being gathered.

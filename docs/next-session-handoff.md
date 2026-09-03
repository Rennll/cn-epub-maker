# Session Handoff

## Current State

V1 is complete and stable.

V2 is complete for its defined scope: the transformation pipeline, CLI orchestration, Intermediate transformation metadata, focused/integration tests, and real TXT → CLI → Pandoc → EPUB black-box validation are all in place.

V2 extends the V1 core rather than replacing it. The completed path is:

Normalize → V2 Transformations → Parser → Intermediate → V1 EPUB Renderer → Validation

The V2 design and migration decisions are recorded in `docs/v2-migration-and-design-decisions.md`. Source code and tests remain the canonical source for implementation details.

## Next Stage: V2.x

The next architectural task is `Intermediate → Book → EPUB` rebuilding.

This is not a missing V2 implementation step. Treat it as a new V2.x feature/evolution that requires its own explicit contract, data-model decisions, implementation plan, and tests.

Before implementation, clarify the responsibilities and boundaries between Intermediate, Book, and EPUB generation. Preserve the completed V1/V2 contracts unless a concrete use case requires an explicit change.

## Important Context

V1 remains the stable structural baseline. V2 adds the completed transformation stage around that baseline.

The V2 content pipeline is:

Normalize → Junk Cleaner → OpenCC → Punctuation → Parser → Intermediate → EPUB → Validation

Full Source Mode remains:

TXT → Normalize → Parser

Do not reopen completed V1/V2 behavior merely for V2.x convenience. Renderer behavior such as HTML whitespace collapsing remains a renderer concern rather than a transformation-stage guarantee.

## Do Not Add Without a New Decision

- Do not treat `Intermediate → Book → EPUB` rebuilding as unfinished V2 work.
- Do not add a separate Whitespace Cleanup transformer.
- Do not introduce heuristic junk detection.
- Do not add arbitrary replacement through Junk Cleaner.
- Do not add global Arabic numeral conversion or automatic chapter renumbering.
- Do not broaden Punctuation Conversion into general Markdown/HTML/code parsing without an explicit contract.
- Do not add arbitrary external OpenCC configuration files without an explicit design decision.
- Do not weaken or bypass the V1 Parser, Intermediate, or Pandoc-first renderer contracts implicitly.

The next session should begin with V2.x architecture/design for the rebuilding path, not with another V2 completion pass.

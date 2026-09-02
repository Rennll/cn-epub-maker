# Session Handoff

## Current State

V1 is complete and is the stable project baseline. Its architecture and behavioral contract are documented in `docs/v1-architecture-decisions.md`.

V2 is not complete. Its current architectural decisions and migration boundaries are documented in `docs/v2-migration-and-design-decisions.md`.

The documentation structure is intentionally split by information lifetime:

- `README.md` — human-facing project entry point.
- `docs/README.md` — AI-oriented documentation map.
- `docs/v1-architecture-decisions.md` — stable V1 contract.
- `docs/v2-migration-and-design-decisions.md` — decided V2 design that is not yet fully implemented.
- `docs/next-session-handoff.md` — temporary state for continuing unfinished work.

## Current Task

The V1 documentation has been condensed into its canonical architecture document, and the V2 planning document has been condensed into its canonical design document.

The remaining project work is V2 implementation. Do not reopen or redesign the completed V1 architecture unless a concrete regression or new requirement requires it.

## Important Context

Use the repository and the canonical V1/V2 documents as the primary sources of truth. Do not recreate information here that can be derived from source code, tests, or those documents.

The key architectural boundary is:

```text
V1 = completed and stable
V2 = decided design, implementation incomplete
Handoff = temporary current-session state
```

V2 must extend the V1 model, Intermediate boundary, parser contract, and Pandoc-first renderer rather than replacing them for legacy compatibility.

The V2 transformation order is:

```text
Normalize
 ↓
Junk Cleaner
 ↓
OpenCC
 ↓
Quote Conversion
 ↓
Parser
 ↓
Intermediate
 ↓
EPUB
 ↓
Validation
```

Full Source Mode disables content transformations but still runs Normalize.

## Next Steps

When beginning the next implementation session:

1. Read `docs/README.md`.
2. Read `docs/v1-architecture-decisions.md` and treat it as the V1 contract.
3. Read `docs/v2-migration-and-design-decisions.md` and treat it as the current V2 design baseline.
4. Inspect the current source tree and tests before deciding which V2 extension is actually ready to implement.
5. Implement one isolated V2 extension at a time, following the order described in the V2 design where the current codebase supports it.
6. Keep the V1 core stable and verify focused tests before the full test suite and integration checks.

This file should be updated whenever the current unfinished work changes. Completed decisions should be moved into the canonical V1/V2 documents rather than accumulated here.

# Session Handoff

## Current State

V1 is complete and stable.

V2 design decisions are recorded in `docs/v2-migration-and-design-decisions.md`, but V2 implementation is incomplete.

## Current Task

Continue V2 implementation. Do not reopen the completed V1 architecture unless a concrete regression or new requirement requires it.

## Important Context

Treat `docs/v1-architecture-decisions.md` as the V1 contract and `docs/v2-migration-and-design-decisions.md` as the current V2 design baseline. Use source code and tests as the canonical source for implementation details.

V2 content transformations are ordered:

Normalize → Junk Cleaner → OpenCC → Quote Conversion → Parser → Intermediate → EPUB → Validation

Full Source Mode disables content transformations but still runs Normalize.

## Next Steps

1. Inspect the current source tree and tests before choosing the next V2 extension.
2. Implement one isolated V2 extension at a time.
3. Add focused tests for each extension before full/integration validation.
4. Keep the V1 core stable.
5. Update this handoff when the unfinished task or next-session state changes.

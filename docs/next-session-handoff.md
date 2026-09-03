# Session Handoff

## Current State

V1 is complete and stable.

The first V2 transformation slice is implemented and has passed focused tests, CLI integration validation, and real TXT → CLI → Pandoc → EPUB black-box validation. V2 as a whole remains incomplete where future features require a separate contract.

The V2 design decisions are recorded in `docs/v2-migration-and-design-decisions.md`. Source code and tests remain the canonical source for implementation details.

## Completed V2 Slice

The following V2 work is complete:

1. Common transformation boundary, result/error/audit contract, and pipeline.
2. Junk Cleaner remove-only semantics, explicit rules, warnings, and statistics.
3. V2 transformation orchestration while preserving the V1 Parser contract.
4. OpenCC with the built-in conversion-profile registry and `s2twp` default.
5. Punctuation Conversion with URL/email protection and idempotent behavior.
6. CLI integration, transformation reporting, and Full Source Mode.
7. Transformation audit metadata persisted in Intermediate `book.json`.
8. Focused tests, CLI/integration tests, and real TXT → EPUB black-box validation.

The intended V2 content pipeline is:

Normalize → Junk Cleaner → OpenCC → Punctuation → Parser → Intermediate → EPUB → Validation

The real EPUB path has been validated end-to-end. Final EPUB assertions account for renderer behavior such as HTML whitespace collapsing; such renderer behavior is not treated as a transformation-stage guarantee.

## Important Context

Treat `docs/v1-architecture-decisions.md` as the V1 contract and `docs/v2-migration-and-design-decisions.md` as the current V2 design baseline. Use source code and tests as the canonical source for implementation details.

Junk Cleaner is remove-only and user-configured. Rules execute sequentially in user-specified order. Supported scopes are `line` and `block`; supported matchers are `exact`, `contains`, and `regex`. Invalid regex is a recoverable warning for that rule, so later rules continue. Pure whitespace lines produced/preserved at the Junk Cleaner boundary are canonicalized to `""`; lines containing non-whitespace content are otherwise not whitespace-normalized.

OpenCC is enabled by default with profile `s2twp`. The first implementation exposes built-in profiles only; invalid profiles and initialization/dependency failures are fatal. OpenCC operates on the full text after Junk Cleaner.

Punctuation Conversion runs after OpenCC and before Parser. It handles the agreed Taiwan full-width punctuation/context rules, ellipsis conversion, direct quote conversion, and URL/email protection. It must be idempotent and must not perform general whitespace cleanup or content repair.

Full Source Mode disables content transformations but still runs Normalize:

TXT → Normalize → Parser

## Next Steps

The first V2 transformation slice is complete. Do not reopen the completed V1 architecture or transformation stages unless a concrete regression or new requirement requires it.

A future Intermediate → Book → EPUB rebuilding capability, if required, is a separate feature and needs its own explicit contract, implementation, and tests. It is not part of the completed transformation slice.

Regex helper/testing UX remains a future enhancement and is not part of the first implementation.

## Do Not Add

- No separate Whitespace Cleanup transformer.
- No heuristic junk detection.
- No arbitrary replacement through Junk Cleaner.
- No global Arabic numeral conversion.
- No chapter renumbering.
- No broad Markdown/HTML/code parsing for Punctuation beyond the explicitly protected URL/email cases.
- No arbitrary external OpenCC config files in the first implementation.

Keep each extension isolated and preserve the V1 model, Intermediate boundary, parser behavior, and Pandoc-first renderer unless a concrete requirement explicitly changes them.

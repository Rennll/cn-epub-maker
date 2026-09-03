# Session Handoff

## Current State

V1 is complete and stable.

V2 design decisions are recorded in `docs/v2-migration-and-design-decisions.md`, but V2 implementation is incomplete.

The V2 design is now implementation-ready for the first transformation slice. Whitespace Cleanup was explicitly removed from the plan after verifying that the existing Parser already treats whitespace-only and consecutive blank lines as paragraph boundaries without creating empty paragraphs.

## Current Task

Continue V2 implementation. Do not reopen the completed V1 architecture unless a concrete regression or new requirement requires it.

## Important Context

Treat `docs/v1-architecture-decisions.md` as the V1 contract and `docs/v2-migration-and-design-decisions.md` as the current V2 design baseline. Use source code and tests as the canonical source for implementation details.

The intended V2 content pipeline is:

Normalize → Junk Cleaner → OpenCC → Punctuation → Parser → Intermediate → EPUB → Validation

Junk Cleaner is remove-only and user-configured. Rules execute sequentially in user-specified order. Supported scopes are `line` and `block`; supported matchers are `exact`, `contains`, and `regex`. Invalid regex is a recoverable warning for that rule, so later rules continue. Pure whitespace lines produced/preserved at the Junk Cleaner boundary are canonicalized to `""`; lines containing non-whitespace content are otherwise not whitespace-normalized.

OpenCC is enabled by default with profile `s2twp`. The first implementation exposes built-in profiles only; invalid profiles and initialization/dependency failures are fatal. OpenCC operates on the full text after Junk Cleaner.

Punctuation Conversion runs after OpenCC and before Parser. It handles the agreed Taiwan full-width punctuation/context rules, ellipsis conversion, direct quote conversion, and URL/email protection. It must be idempotent and must not perform general whitespace cleanup or content repair.

Full Source Mode disables content transformations but still runs Normalize:

TXT → Normalize → Parser

Regex helper/testing UX is a future enhancement and is not part of the first implementation.

## Next Steps

1. Establish the common transformation boundary/result/error contract and reporting model.
2. Implement Junk Cleaner configuration and remove-only semantics, including pure-whitespace-line canonicalization.
3. Implement transformation pipeline/orchestration without changing the existing V1 Parser contract.
4. Add OpenCC and its built-in conversion-profile registry.
5. Add Punctuation Conversion.
6. Integrate the V2 configuration and transformation pipeline into the CLI.
7. Add transformation metadata at the Intermediate boundary.
8. Add focused tests for each extension, then run full regression/integration validation.

## Do Not Add

- No separate Whitespace Cleanup transformer. The current Parser already handles multiple consecutive blank lines and whitespace-only lines as paragraph boundaries.
- No heuristic junk detection.
- No arbitrary replacement through Junk Cleaner.
- No global Arabic numeral conversion.
- No chapter renumbering.
- No broad Markdown/HTML/code parsing for Punctuation beyond the explicitly protected URL/email cases.
- No arbitrary external OpenCC config files in the first implementation.

Keep each extension isolated and preserve the V1 model, Intermediate boundary, parser behavior, and Pandoc-first renderer unless a concrete requirement explicitly changes them.

# Next Session Handoff

## Current state

V1 is complete and should now be treated as the stable baseline. Phase 1–6 were completed, including model/serialization, normalization, TXT parsing, intermediate JSON, Pandoc-first EPUB rendering, EPUB structure validation, and EPUBCheck integration.

PR #1 was merged back into `main`. Do not reopen the V1 architecture work unless a concrete regression or requirement requires it.

The repository currently contains these important design documents:

- `docs/v1-architecture-decisions.md`
- `docs/v1-readme-zh-TW.md`
- `docs/v2-migration-and-design-decisions.md`

The V2 migration/design document is the primary record of the decisions made during planning.

## V1 principle

V1 is intentionally a minimal rewrite, not a complete clone of the legacy `cn-epub-maker` behavior.

The stable V1 pipeline is:

```text
TXT
 ↓
Normalize
 ↓
Parser
 ↓
Intermediate
 ↓
Markdown
 ↓
Pandoc
 ↓
EPUB
 ↓
Validation
```

The goal is predictable behavior, preservation of source meaning, and a clean architecture. Legacy feature parity must not be added merely because the old implementation had a feature.

## V2 direction

V2 should extend the V1 architecture rather than replace it.

The planned transformation pipeline is:

```text
Normalize
 ↓
optional Junk Cleaner
 ↓
optional OpenCC
 ↓
optional Quote Conversion
 ↓
Parser
 ↓
Intermediate
 ↓
Pandoc EPUB
 ↓
Validation
```

The key architectural distinction is:

- Normalize makes the source representation stable and usable.
- Transformations intentionally change content according to explicit configuration.
- Parser determines document structure and should not silently perform content transformations.
- Renderer determines EPUB presentation and packaging concerns.

## Decisions already made

### OpenCC

Keep OpenCC in V2 because the primary use case is converting Simplified Chinese sources to Traditional Chinese output.

OpenCC should be enabled by default, while retaining a conversion-profile abstraction so other profiles can be supported later. Users must be able to disable it.

### Junk Cleaner

Keep Junk Cleaner, but redesign it as an explicit user-configured, remove-only transformation.

Rules are stored in a separate rules file rather than being mixed into general book configuration.

Supported semantic targets:

- `line`: one normalized source line.
- `block`: a continuous text block separated by blank lines.

Supported matchers:

- `exact`
- `contains`
- `regex`

A successful match always removes the entire target. `contains` and `regex` do not perform substring replacement.

Rules execute in user-specified order. Each rule receives the previous rule's output.

A zero-match rule is normal and is not a warning. Cleaner should report per-rule statistics, including the number of targets removed.

Invalid rules, such as invalid regular expressions, produce warnings and are skipped; later valid rules continue to run.

Cleaner does not know about Chapter or Paragraph because it runs before parsing. It must not cross line/block boundaries or perform document restructuring.

### Quote conversion

Keep quote conversion as an independent transformation. It should have predictable, explicitly tested mappings and should be idempotent.

### Full Source Mode

Retain a complete-source mode in V2.

It means no content transformations:

```text
Normalize
 ↓
Parser
```

Normalize still runs. Full Source Mode is therefore not byte-for-byte preservation. Encoding interpretation, BOM, newline representation, and the defined leading full-width-space normalization may still change the source representation.

### Transformation failure policy

Use two classes of failure:

1. Recoverable problem: warning, skip the affected transformation/rule, continue generation.
2. Unrecoverable problem that makes the output untrustworthy: error and stop output generation.

This is consistent with the V1 validation policy: non-blocking problems should be visible as warnings rather than unnecessarily preventing EPUB generation.

### Intermediate transformation metadata

Record transformation metadata in Intermediate artifacts for reproducibility and debugging.

Do **not** expose this internal configuration in EPUB metadata.

### Features intentionally not migrated

Do not migrate these legacy behaviors as part of the V2 baseline:

- Arabic numeral conversion.
- Automatic chapter renumbering.
- Legacy heuristic junk detection.
- Arbitrary replacement through Junk Cleaner.

If one of these becomes necessary later, require a concrete use case and a new explicit contract before implementation.

## Open engineering direction

The next architectural pieces to implement or formalize are:

1. A common Transform interface covering input text, output text, statistics, and warnings.
2. OpenCC configuration with a conversion-profile abstraction.
3. Junk Cleaner configuration and implementation according to the agreed contract.
4. Quote Conversion as a separate transformation.
5. Parser configuration for useful structural patterns from the legacy implementation, without coupling it to transformations.
6. Renderer profiles for future EPUB presentation options instead of accumulating renderer conditionals.
7. CLI/library separation so configuration remains the primary representation of build behavior.
8. Reproducible build metadata in Intermediate.

Do not implement all of these as one large migration. Introduce one extension at a time and keep the V1 core stable.

## Recommended development workflow

For each V2 feature:

```text
Review existing contract
 ↓
Ask only product/behavior questions that are still unresolved
 ↓
Write focused failing tests
 ↓
Implement the smallest change
 ↓
Run targeted tests
 ↓
Run full test suite
 ↓
Perform integration sanity check
 ↓
Commit
```

After completing a meaningful group of tests/features, perform a phase-level inventory rather than assuming that passing tests mean the entire phase is complete.

When modifying files through GitHub, first fetch the latest file contents and use its current SHA before writing. Do not use a stale SHA for sequential edits.

## Testing guidance for transformations

Every new transformation should, where applicable, test:

- normal input and expected transformation;
- no-match input remains unchanged and reports zero matches;
- invalid configuration produces a warning and does not block unrelated work;
- repeated application does not introduce unintended changes when idempotence is expected;
- Full Source Mode prevents the transformation from running;
- statistics accurately describe the transformation effect.

Tests should target stable public seams rather than incidental implementation details whenever possible.

## First action for a new session

Before coding, read:

```text
README.md

docs/v1-architecture-decisions.md
docs/v1-readme-zh-TW.md
docs/v2-migration-and-design-decisions.md
docs/next-session-handoff.md
```

Then inspect the legacy implementation only as needed to implement the migration matrix. Do not redo the completed V1 architecture review.

The current project state should be treated as:

> **V1 frozen as the stable core; V2 migration decisions documented; ready to implement the first isolated extension.**

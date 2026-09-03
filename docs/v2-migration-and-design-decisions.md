# V2 Design

## Status

V2 is the completed transformation and integration stage built on top of V1. The decisions in this document define the V2 architectural baseline and its completed scope.

V2 extends completed V1. It does not replace the V1 model, Intermediate boundary, parser contract, or Pandoc-first renderer merely to reproduce legacy behavior.

## Relationship to V1

V1 remains the stable core:

Normalize → Parser → Intermediate → Pandoc EPUB → Validation

V2 adds isolated transformation and orchestration capabilities around that core. Legacy compatibility is subordinate to predictable behavior, explicit configuration, and preservation of the V1 architecture.

## Migration Decisions

| Legacy behavior | V2 decision | Boundary |
|---|---|---|
| OpenCC Simplified → Traditional | Keep | Enabled by default; configurable and extensible by conversion profile |
| Junk Cleaner | Keep | User-configured, remove-only, explicit target and matcher |
| Quote/Punctuation Conversion | Keep | Independent transformation with explicit/idempotent behavior |
| Arabic numeral conversion | Do not migrate | Avoid changing dates, IDs, URLs, formulas, versions, or other numeric content |
| Chapter renumbering | Do not migrate | Preserve source numbering and references |

V2 is not intended to become a complete behavioral clone of the legacy implementation.

## Architecture

### Transform Pipeline

The V2 content pipeline is:

TXT → Normalize → Junk Cleaner → OpenCC → Punctuation → Parser → Intermediate → EPUB → Validation

The order is intentional. Content transformations are separate from structural parsing and should not be silently embedded in Parser or Renderer behavior.

### Common Transform Contract

Each transformation receives text and, when successful, produces a `TransformResult` conceptually containing:

- `text`: transformed text.
- `changed`: whether the output text differs from the input.
- `warnings`: recoverable problems encountered during the transformation.
- `stats`: optional transformer-specific execution statistics.
- `metadata`: optional information describing the transformation/configuration used.

`text`, `changed`, and `warnings` are common fields. `stats` is intentionally not a universal schema: each transformer may report only statistics that are meaningful for it. `metadata` describes configuration or transformation identity rather than execution counts.

Zero changes and zero matches are normal successful results and do not produce warnings.

The CLI is responsible for presenting transformation results; transformers should return structured information rather than constructing CLI-specific messages. For example, OpenCC may be displayed simply as `✅ 使用 OpenCC（s2twp）` rather than reporting character-level conversion counts.

Transformers do not directly modify Book, Chapter, Volume, EPUB, or other structural objects, and they do not invoke other transformers. The pipeline owns transformation order.

### Failure and Auditability

Recoverable problems produce warnings and skip only the affected operation/rule when possible. The pipeline continues. Unrecoverable problems, or output that can no longer be trusted, produce an error and stop the pipeline.

Errors are not represented as successful `TransformResult` values. A transformer reports a structured error to the pipeline; the pipeline stops subsequent processing, and the CLI renders a concise, user-facing message identifying the responsible transformer and actionable cause when available. Detailed traceback information should be reserved for an explicit debug mode rather than normal CLI output.

Configuration errors and runtime/system errors are both fatal when they prevent trustworthy transformation. For example, an invalid OpenCC profile is a configuration error and must stop the pipeline rather than silently falling back.

Transformation metadata belongs in Intermediate rather than EPUB metadata so transformed output remains auditable and reproducible. Transformations should be deterministic and idempotent where practical.

## Transforms

### OpenCC

OpenCC is retained as a V2 transformation and is enabled by default. The default profile is `s2twp`, matching the legacy implementation. The user may disable OpenCC or select a supported conversion profile.

The transformation applies to the full text after Normalize and Junk Cleaner. OpenCC itself does not perform custom English, URL, email, or prose-context detection; protection/context-sensitive handling belongs to the relevant downstream transformation, such as Punctuation.

The first V2 implementation exposes built-in profile names only. The internal design uses a conversion-profile abstraction/registry so additional built-in profiles can be added later without redesign. Arbitrary external OpenCC configuration files are intentionally out of scope for V2.

An invalid or nonexistent profile is a configuration error: the pipeline stops and the user is told to provide a valid profile. There is no silent fallback. OpenCC initialization/dependency failures are also fatal when the transformation cannot be performed reliably.

Zero changes are normal success. OpenCC does not need character-level conversion statistics; profile identity is sufficient for normal reporting, e.g. `✅ 使用 OpenCC（s2twp）`.

OpenCC should be deterministic and idempotent.

### Junk Cleaner

Junk Cleaner is a parser-preprocessing transformation. Users explicitly select what counts as junk; there is no heuristic junk detection.

Its configuration is separate from general book configuration. A rule specifies a target and matcher:

- `line` targets one normalized source line and cannot cross a newline.
- `block` targets one or more continuous non-blank lines. One or more blank lines form the boundary between blocks.
- `exact`, `contains`, and `regex` are supported matchers.

A matching rule removes the entire target. `contains` and `regex` do not replace only the matching substring.

`exact` means the complete target equals the configured pattern. It does not trim or otherwise normalize the target before comparison.

`regex` uses the target determined by `scope`: one line for `line`, or one current block for `block`. Regex matching uses search semantics. No additional regex flags are exposed in the V2 implementation. An invalid regex is a warning; that rule is skipped and later rules continue. A syntactically valid regex that matches very broadly is still valid user configuration and is not heuristically rejected.

Rules execute in user-specified order, with each rule operating on the result of the previous rule. For each `block` rule, blocks are re-formed from the current text after previous rules have run.

Removing a block removes only the block's non-blank lines. Boundary blank lines are not removed, merged, or newly created by Junk Cleaner.

As an output canonicalization rule, any line that contains only whitespace characters is represented as an empty line (`""`) after Junk Cleaner processing. This includes spaces, tabs, and full-width whitespace. Lines containing any non-whitespace content are otherwise unchanged; Junk Cleaner does not trim trailing whitespace, normalize indentation, or perform general whitespace cleanup. This canonicalization does not collapse multiple blank lines, which remain the Parser's responsibility for paragraph boundaries.

The cleaner operates before Parser and therefore has no knowledge of chapters, paragraphs, volumes, or EPUB structure. It must not infer structure, cross configured boundaries, or introduce a second normalization layer.

Each rule reports match/removal counts. Zero matches are normal. Invalid regex/configuration at rule level is a warning when the affected rule can be safely skipped; later rules continue.

Junk Cleaner is remove-only. Arbitrary replacement is intentionally a separate future transformation concern.

### Punctuation Conversion

Punctuation Conversion is an independent transformation that converts applicable Simplified-Chinese-style punctuation to common Taiwan Traditional Chinese full-width punctuation while preserving English content and punctuation outside Chinese context.

Direct quote conversions are:

- `“` → `「`
- `”` → `」`
- `‘` → `『`
- `’` → `』`

In Chinese context, the following conversions apply:

- `,` → `，`
- `!` → `！`
- `?` → `？`
- `:` → `：`
- `;` → `；`
- `.` → `。` when it is a Chinese sentence-ending period
- three or more consecutive ASCII periods → one `……`

Existing `……` remains unchanged. The ellipsis rule is evaluated before the single-period rule.

Parentheses `(` `)`, square brackets `[` `]`, and curly braces `{` `}` remain unchanged. Other ASCII symbols such as `/`, `\\`, `|`, `_`, `=`, `+`, `-`, `*`, `%`, `#`, `@`, `<`, `>`, and `~` are not converted by this transformer in the V2 implementation.

Chinese-context detection is local rather than based on whether an entire line contains Chinese. Punctuation is considered in Chinese context when the nearest meaningful preceding content is Chinese CJK text; English and numbers do not establish Chinese context. Leading punctuation with no preceding Chinese context is preserved. Whitespace does not itself establish or remove context.

Obvious URLs and email addresses are protected from punctuation conversion. The V2 implementation does not attempt broad Markdown/HTML/code parsing beyond the explicitly protected URL/email cases.

The transform does not repair quote pairing, collapse repeated `?`/`!`, remove content, normalize whitespace, or guess author intent. For example, `什麼???` becomes `什麼？？？`, not a single `？`.

Punctuation Conversion is idempotent and runs after OpenCC and before Parser.

## Modes

### Full Source Mode

Full Source Mode runs:

TXT → Normalize → Parser

Content transformations are disabled, but Normalize still runs. Therefore this mode is source-content-preserving rather than byte-for-byte preservation: encoding interpretation, BOM handling, newline normalization, and the defined leading full-width-space normalization may still change representation.

## Parser and Renderer Extensions

### Parser Configuration

Configurable volume/chapter patterns may be retained where they provide useful structural flexibility. Parser configuration remains structural; it must not become a hidden home for OpenCC, junk cleaning, punctuation conversion, global numeral conversion, chapter renumbering, or whitespace cleanup.

### Renderer Profiles

Future renderer profiles may support presentation choices such as horizontal or vertical layout. Pandoc-first remains the foundation; project-specific assembly should own only responsibilities that Pandoc cannot safely or conveniently handle.

## Configuration and CLI

The configuration model is the primary interface for behavior; the CLI is a frontend to that model. CLI options should expose meaningful configuration without turning unrelated implementation details into a growing collection of flags.

The exact Intermediate schema should follow the existing contract. Transformation metadata belongs to Intermediate as part of the audit/reproducibility boundary, not as EPUB metadata.

Regex errors should be presented with enough information to identify and repair the rule, including the rule identity, configured pattern, and underlying regex error when available. Future UX may provide regex testing/help, but such assistance is not required for the completed V2 scope.

## Non-goals

V2 does not include global Arabic numeral conversion, automatic chapter renumbering, heuristic junk detection, arbitrary replacement through Junk Cleaner, broad whitespace cleanup by Junk Cleaner, or byte-for-byte source preservation. It also does not justify rebuilding the V1 model, Intermediate boundary, or Pandoc-first renderer merely for legacy compatibility. Any future exception requires a concrete use case and an explicit behavioral contract.

## Implementation Status

The V2 implementation is complete for the scope defined above. The completed work includes the common transformation contract and pipeline, Junk Cleaner, OpenCC, Punctuation Conversion, CLI orchestration, transformation audit metadata at the Intermediate boundary, focused and integration tests, and real TXT → CLI → Pandoc → EPUB black-box validation.

The completed V2 path preserves the V1 structural core:

Normalize → V2 Transformations → Parser → Intermediate → V1 EPUB Renderer → Validation

## Future Evolution: V2.x

`Intermediate → Book → EPUB` rebuilding is not a missing V2 implementation step. It is a separate V2.x feature/architectural evolution and requires its own explicit data-model contract, implementation, and tests.

Other future capabilities may also be considered under V2.x when they extend or revise the completed V2 architecture without changing the V1/V2 contracts implicitly.

## Design Principles

Each extension should remain isolated, keep the V1 core stable, and receive focused tests before integration validation. Changes to completed V1/V2 contracts require a concrete use case and an explicit behavioral decision rather than being inferred from implementation convenience.

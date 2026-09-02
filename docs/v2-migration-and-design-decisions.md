# V2 Design

## Status

V2 is proposed design and implementation is incomplete. The decisions in this document are the current architectural baseline, not a claim that every item is already implemented.

V2 extends completed V1. It should not replace the V1 model, Intermediate boundary, parser contract, or Pandoc-first renderer merely to reproduce legacy behavior.

## Relationship to V1

V1 remains the stable core:

Normalize → Parser → Intermediate → Pandoc EPUB → Validation

V2 adds isolated extension points around that core. Legacy compatibility is subordinate to predictable behavior, explicit configuration, and preservation of the V1 architecture.

## Migration Decisions

| Legacy behavior | V2 decision | Boundary |
|---|---|---|
| OpenCC Simplified → Traditional | Keep | Enabled by default; configurable and extensible by conversion profile |
| Junk Cleaner | Keep | User-configured, remove-only, explicit target and matcher |
| Quote Conversion | Keep | Independent transformation with explicit/idempotent behavior |
| Arabic numeral conversion | Do not migrate | Avoid changing dates, IDs, URLs, formulas, versions, or other numeric content |
| Chapter renumbering | Do not migrate | Preserve source numbering and references |

V2 is not intended to become a complete behavioral clone of the legacy implementation.

## Architecture

### Transform Pipeline

The default V2 pipeline is:

TXT → Normalize → Junk Cleaner → OpenCC → Quote Conversion → Parser → Book → Intermediate → EPUB → Validation

The order is intentional. Content transformations are separate from structural parsing and should not be silently embedded in Parser or Renderer behavior.

### Transform Contract

A transformation receives text and produces transformed text plus observable statistics and warnings. Transformations should be independently testable, and zero matches are a normal result rather than a failure.

### Failure and Auditability

Recoverable problems produce warnings and skip the affected transformation or rule. Unrecoverable problems, or output that can no longer be trusted, produce an error and stop the pipeline. Zero matches are not failures.

Transformation metadata belongs in Intermediate rather than EPUB metadata so transformed output remains auditable and reproducible. Transformations should be deterministic and idempotent where practical.

## Transforms

### OpenCC

OpenCC is retained as a V2 transformation and is enabled by default. It can be disabled, and the design keeps a conversion-profile abstraction for future profiles. It follows the common transformation failure policy.

### Junk Cleaner

Junk Cleaner is a parser-preprocessing transformation. Users explicitly select what counts as junk; there is no heuristic junk detection.

Its configuration is separate from general book configuration. A rule specifies a target and matcher:

- `line` targets one normalized source line and cannot cross a newline.
- `block` targets a continuous text block separated by blank lines and cannot cross a blank-line boundary.
- `exact`, `contains`, and `regex` are supported matchers.

A matching rule removes the entire target. `contains` and `regex` do not replace only the matching substring.

Rules execute in user-specified order, with each rule retargeting the result of the previous rule. The cleaner operates before Parser and therefore has no knowledge of chapters, paragraphs, volumes, or EPUB structure. It must not infer structure, cross configured boundaries, or introduce a second normalization layer.

Each rule reports match/removal counts. Zero matches are normal. Invalid configuration or regex is a warning; the invalid rule is skipped and later rules continue.

Junk Cleaner is remove-only. Arbitrary replacement is intentionally a separate future transformation concern.

### Quote Conversion

Quote Conversion is independent of the other transformations. Defined curly-quote forms are converted to Chinese quotation forms such as `「」` and `『』`; already-correct Chinese quotation marks are preserved. The transform should be explicit and idempotent and runs after Junk Cleaner and OpenCC.

## Modes

### Full Source Mode

Full Source Mode runs:

TXT → Normalize → Parser

Content transformations are disabled, but Normalize still runs. Therefore this mode is source-content-preserving rather than byte-for-byte preservation: encoding interpretation, BOM handling, newline normalization, and the defined leading full-width-space normalization may still change representation.

## Parser and Renderer Extensions

### Parser Configuration

Configurable volume/chapter patterns may be retained where they provide useful structural flexibility. Parser configuration remains structural; it must not become a hidden home for OpenCC, junk cleaning, quote conversion, global numeral conversion, or chapter renumbering.

### Renderer Profiles

Future renderer profiles may support presentation choices such as horizontal or vertical layout. Pandoc-first remains the foundation; project-specific assembly should own only responsibilities that Pandoc cannot safely or conveniently handle.

## Configuration and CLI

The configuration model is the primary interface for behavior; the CLI is a frontend to that model. CLI options should expose meaningful configuration without turning unrelated implementation details into a growing collection of flags.

The exact Intermediate schema should follow the existing contract. Transformation metadata belongs to Intermediate as part of the audit/reproducibility boundary, not as EPUB metadata.

## Non-goals

V2 does not include global Arabic numeral conversion, automatic chapter renumbering, heuristic junk detection, arbitrary replacement through Junk Cleaner, or byte-for-byte source preservation. It also does not justify rebuilding the V1 model, Intermediate boundary, or Pandoc-first renderer merely for legacy compatibility. Any future exception requires a concrete use case and an explicit behavioral contract.

## Implementation Order

1. Establish the common transformation boundary, failure policy, and reporting.
2. Add the OpenCC conversion profile.
3. Add Junk Cleaner configuration and remove-only semantics.
4. Add Quote Conversion.
5. Add useful structural Parser configuration.
6. Add renderer profiles.
7. Stabilize the configuration/library and CLI boundary.
8. Add Intermediate transformation metadata.

Each extension should remain isolated, keep the V1 core stable, and receive focused tests before full/integration validation.

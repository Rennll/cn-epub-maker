# V2.x Configuration Model Architecture

## Status

This document defines the V2.x configuration architecture for `cn-epub-maker`.

It is an architectural refinement of V2. It does not replace the V1 structural model, the V2 transformation contracts, the Intermediate boundary, the parser contract, or the Pandoc-first renderer.

The central architectural statement is:

> `ConversionRequest` is a resolved application configuration/request, not an execution plan.

## Purpose

The Configuration Model provides a stable application-level interface for describing one conversion operation. It separates user intent from the syntax used to express that intent and prevents CLI-specific structures from becoming application-wide contracts.

The same application-level model should be usable by multiple frontends in the future, including:

- CLI;
- configuration files;
- Python/API callers;
- GUI or other future interfaces.

The architectural flow is:

```text
CLI / Config File / API
        ↓
Configuration Resolution
        ↓
ConversionRequest
        ↓
Execution
        ↓
Book / EPUB / Provenance
```

## Architectural Principles

### Configuration is the application-level behavior interface

Configuration describes what the application should do for a particular conversion. The CLI is one frontend to that model, not the model itself.

### `argparse.Namespace` is not the application configuration model

`argparse.Namespace` is an adapter representation produced by the CLI parser. Application code should not depend on it.

The intended boundary is:

```text
CLI syntax → parsed CLI values → configuration resolution → ConversionRequest
```

### Not everything that changes output is Configuration

A value belongs in application configuration when it represents user- or application-selectable policy or request data. Output impact alone is not sufficient.

The architecture distinguishes among:

- request data;
- user/application policy;
- system definitions;
- component configuration;
- runtime state;
- execution results;
- execution provenance.

For example, `paragraph_mode` is Parser Policy, while chapter recognition patterns are Parser Grammar and newline normalization is a System Definition.

### Configuration describes policy, not implementation

Configuration expresses What or Whether. Components own How.

For example:

```text
opencc.profile = "s2twp"
```

selects an OpenCC policy. It does not mean that `ConversionRequest` owns an `OpenCCTransformer` instance.

## ConversionRequest

`ConversionRequest` represents one complete, resolved conversion request.

Conceptually:

```text
ConversionRequest
├── source
├── book_metadata: BookMetadata
├── destination
└── policy: ConversionPolicy
    ├── encoding
    ├── parser: ParserPolicy
    │   └── paragraph_mode
    ├── transformations: TransformationPolicy
    │   ├── opencc: OpenCCConfig
    │   │   ├── enabled
    │   │   └── profile
    │   ├── punctuation_enabled
    │   └── junk_cleaner: JunkCleanerConfig
    │       └── rules: JunkRule[...]
    └── full_source
```

This is a semantic model. Not every conceptual grouping must become a dedicated Python type. A type should be introduced when it has its own responsibility, invariant, validation, or public API value.

### Request versus Book

`ConversionRequest` is an operation-level concept. `Book` is the domain/result model produced by parsing.

For example, book title may be supplied as request metadata and then copied into the resulting `Book`. That does not make title Parser Configuration.

```text
ConversionRequest
      ↓
    Parser
      ↓
     Book
```

### Request versus execution plan

`ConversionRequest` is not an execution plan.

It should not contain:

- transformer instances;
- parser instances;
- renderer instances;
- execution step lists;
- runtime state;
- actual detected encoding;
- transformation audit objects;
- `Book`;
- EPUB output;
- execution results.

Execution derives its runtime objects and steps from the request.

The intended relationship is:

```text
Resolved Configuration
        ↓
ConversionRequest
        ↓
Execution
        ↓
Execution Result / Provenance
```

### Immutability

After resolution, `ConversionRequest` is logically immutable. Execution reads the request but does not modify it.

The architecture does not currently mandate a specific implementation such as `dataclass(frozen=True)`. Deep immutability is an implementation concern. Nested configuration should follow the same read-only semantic contract.

`ConversionRequest` must not become an execution context that is progressively populated with runtime facts.

## BookMetadata

Book metadata currently consists of:

- `title`;
- `author`;
- `language`;
- `cover`.

These values belong to Book/domain metadata rather than Parser Configuration.

Parser may use them when constructing a `Book`. Renderer consumes the resulting Book metadata when producing EPUB metadata and assets.

## ConversionPolicy

`ConversionPolicy` describes how this conversion should behave.

Its current conceptual structure is:

```text
ConversionPolicy
├── encoding
├── parser
├── transformations
└── full_source
```

The model intentionally does not introduce `ConversionPolicy.pipeline.full_source`; `full_source` is already a direct Conversion Policy because that is its actual semantic responsibility.

## Encoding Policy

The application-level encoding policy is:

```text
encoding = "auto" | explicit encoding name
```

`"auto"` is an explicit policy value, not an unset value.

The application default is therefore:

```text
encoding = "auto"
```

Requested encoding and actual encoding must remain separate.

For example:

```text
Request:
    encoding = "auto"

Runtime:
    actual encoding = "gb18030"
```

The actual detected encoding is runtime/provenance information. It must not be written back into or mutate the `ConversionRequest`.

The storage and schema of detailed provenance remain a separate architectural decision.

## Parser Policy and Parser Grammar

The current user-facing Parser Policy is:

```text
ParserPolicy
└── paragraph_mode
```

Supported values are currently `wrapped` and `line`, with `wrapped` as the application default.

`paragraph_mode` is configuration because it is a user-selectable policy that changes semantic paragraph structure.

By contrast, `volume_pattern`, `chapter_pattern`, and related recognition patterns are Parser Grammar. Their current function-level configurability does not by itself make them general user-facing application configuration.

Parser Grammar remains owned by the parser unless a future product requirement explicitly exposes custom grammar as public configuration.

## Transformation Policy

Transformation Policy describes user-facing transformation behavior:

```text
TransformationPolicy
├── opencc
├── punctuation_enabled
└── junk_cleaner
```

Transformers remain runtime components. They do not receive or interpret CLI syntax.

### OpenCC

The conceptual configuration is:

```text
OpenCCConfig
├── enabled
└── profile
```

The current application default is OpenCC enabled with profile `s2twp`.

`--no-opencc` resolves to `opencc.enabled = false`.

Selecting a profile resolves to the requested profile with OpenCC enabled.

Whether a profile is valid is OpenCC component-specific validation and remains owned by the OpenCC component.

### Punctuation

The current policy is represented by `punctuation_enabled`.

A separate `PunctuationConfig` type is not required while punctuation has only one independent application-level setting. It may be introduced later if the component develops multiple independently meaningful policy values.

### Junk Cleaner

The conceptual configuration is:

```text
JunkCleanerConfig
└── rules: JunkRule[...]
```

The existing `JunkRule` already represents configuration data with `target`, `matcher`, and `pattern`. A separate `JunkRuleConfig` type is not required unless a future responsibility requires the separation of public schema from the current rule representation.

The central configuration model may carry `JunkCleanerConfig`, but it must not absorb JunkCleaner implementation semantics such as regex compilation, matching algorithms, block construction, or runtime state.

## Full Source Mode

`full_source` is a Conversion Policy / pipeline execution policy.

When `full_source = true`, the effective behavior is to bypass the transformation pipeline after Normalize.

Configuration resolution may therefore derive the effective transformation state as:

```text
full_source = true
        ↓
opencc.enabled = false
punctuation_enabled = false
junk_cleaner = disabled / empty effective rules
```

The cross-field semantics belong to Configuration Resolution. Individual transformers do not need to know that Full Source Mode exists.

Full Source Mode does not imply byte-for-byte source preservation. Normalize still performs its defined source interpretation and normalization behavior.

## Configuration Resolution

The Configuration Resolver is a strict decision layer.

Its responsibility is:

> Configuration Resolver takes one or more user-facing configuration inputs and resolves them, according to application defaults, precedence rules, and cross-field semantics, into a complete and executable `ConversionRequest`. It does not execute conversion and does not own component-specific runtime semantics.

The resolution flow is:

```text
CLI / Config File / API
       ↓
Configuration Resolver
       ├── defaults
       ├── precedence
       ├── cross-field semantics
       └── application-level validation
       ↓
ConversionRequest
```

### Resolver responsibilities

The Resolver may:

1. apply application defaults;
2. apply configuration-source precedence;
3. map user-facing values into the application model;
4. resolve cross-field semantics;
5. validate application-level invariants;
6. produce the resolved `ConversionRequest`.

### Resolver non-responsibilities

The Resolver must not:

- read source files;
- decode source text;
- detect actual encoding;
- normalize text;
- instantiate transformers;
- compile JunkCleaner regexes;
- execute transformations;
- parse chapters;
- construct `Book`;
- render EPUB;
- invoke Pandoc;
- write output files;
- perform runtime/environment validation.

The Resolver is a decision layer, not a conversion manager.

## Defaults and Precedence

Application-level defaults have one authority: the Configuration Model / Resolver.

The CLI parser should not become a second application-default authority through `argparse default=` values. Unspecified CLI values should remain distinguishable from explicit user values until resolution.

The intended future precedence is:

```text
explicit CLI
    >
explicit config file
    >
application default
```

Configuration files are not required by this document; the precedence model is defined in preparation for future support.

Component-level convenience defaults may remain for standalone component use, but they must not override application policy resolved by the Resolver.

## Validation Layers

Validation is divided into three layers:

```text
Configuration / Resolver
        ↓
Component
        ↓
Runtime / Environment
```

### Configuration-level validation

The Resolver validates application-level structure and policy, including required fields, basic types, supported policy values, and cross-field invariants.

For example, `paragraph_mode` must be one of the application-supported values.

### Component-level validation

Components validate their own semantic configuration.

Examples include:

- supported OpenCC profiles;
- JunkCleaner matcher semantics;
- regex compilation;
- component-specific constraints.

The Resolver may understand the public component configuration schema, but it must not duplicate component implementation semantics.

### Runtime validation

Runtime validation covers actual environment and execution conditions, such as:

- source existence;
- filesystem access;
- decoding success;
- Pandoc availability;
- EPUBCheck availability;
- successful output generation.

Configuration errors should not be indiscriminately converted into generic runtime errors, and component-specific error semantics should be preserved.

## Runtime State and Provenance

The following are not part of `ConversionRequest`:

- actual detected encoding;
- transformer instances;
- parser/renderer instances;
- runtime execution state;
- `TransformAudit`;
- runtime warnings generated during execution;
- `Book`;
- EPUB output;
- validation results.

These describe what actually happened rather than what the user requested.

For example:

```text
Request:
    encoding = auto

Runtime:
    actual encoding = gb18030

Execution:
    OpenCC executed
    JunkCleaner executed
    Punctuation executed

Provenance:
    TransformAudit(...)
```

## Intermediate Boundary

The existence of `ConversionRequest` does not change the existing Intermediate contract.

Intermediate remains primarily a serialization of the `Book` plus established transformation audit/provenance metadata.

The resolved request should not simply be embedded wholesale into the Book serialization.

Future reproducibility requirements may justify recording selected resolved policy or runtime facts as provenance, but that is a separate architecture decision.

## Execution Boundaries

The intended application architecture is:

```text
CLI Adapter
  ↓
Configuration Resolver
  ↓
ConversionRequest
  ↓
Execution
  ├── Input / Decode
  ├── Normalize
  ├── Transform
  ├── Parser
  ├── Validation
  ├── Intermediate
  ├── Renderer
  └── EPUB Validation
```

Each stage should consume only the configuration or data it actually needs.

The entire `ConversionRequest` should not be passed through every stage merely as a generic container.

### Input

Input handling receives the source and encoding policy it needs. It should not depend on `argparse.Namespace` or the complete CLI argument set.

### Normalize

Normalize remains a system-defined source interpretation/normalization layer. It does not become a generic configuration consumer.

### Transform

The transformation layer receives `TransformationPolicy` or the corresponding component configuration. It does not receive CLI syntax.

### Parser

The parser remains responsible for structural parsing and consumes parser-specific policy/data. It does not need to understand the entire application request.

### Renderer

The renderer consumes the `Book` and rendering-specific inputs. It should not depend on CLI syntax or the application request as a generic configuration object.

### Intermediate

Intermediate serializes the established domain structure and provenance/audit information. It is not an execution context.

## Responsibility Matrix

| Concept | Owner / Layer |
|---|---|
| CLI flags | CLI Adapter |
| Config file syntax | Configuration Adapter |
| Application defaults | Configuration Resolver |
| Precedence | Configuration Resolver |
| Cross-field semantics | Configuration Resolver |
| `ConversionRequest` | Application Model |
| Book metadata | Domain / Request Model |
| Encoding policy | Conversion Policy |
| Actual encoding | Runtime / Provenance |
| Normalize rules | System Definition |
| Paragraph mode | Parser Policy |
| Chapter/volume patterns | Parser Grammar |
| OpenCC policy | Transformation Policy |
| OpenCC profile semantics | OpenCC Component |
| JunkCleaner rules | JunkCleaner Configuration |
| Junk matching semantics | JunkCleaner Component |
| Transformer instances | Runtime |
| `TransformAudit` | Execution Provenance |
| `Book` | Domain Model / Result |
| EPUB | Final Artifact |
| EPUB validation | Validation / Runtime |

## Refactoring Direction

The primary change is not renaming `args` to `config`. The architectural boundary must change.

Current conceptual flow:

```text
CLI
 ↓
argparse.Namespace
 ↓
build(args)
 ↓
stages read CLI arguments directly
```

Target flow:

```text
CLI
 ↓
CLI Adapter
 ↓
Configuration Resolver
 ↓
ConversionRequest
 ↓
Application Execution
 ↓
stages receive only relevant policy/data
```

This implies, for example:

- `build()` should no longer use an argparse namespace as its application contract;
- transformation orchestration should receive transformation policy rather than CLI arguments;
- input handling should receive source and encoding policy rather than the whole request;
- `parse_lines()` should remain parser-specific rather than accepting the entire request;
- rendering should not depend on CLI arguments or the entire request.

## Anti-Patterns

The implementation must avoid the following:

### God Config

Do not create a configuration object that knows all component implementation details.

### Generic Config Passing

Do not pass the complete `ConversionRequest` to every stage simply because it is convenient.

### Configuration-owned Runtime Objects

Do not make configuration construct or own transformer, parser, renderer, or other runtime instances.

### Duplicate Application Defaults

Do not let CLI, Resolver, and components independently claim authority over application defaults.

### Request Mutation

Do not write runtime facts, actual encoding, audits, results, or execution state back into the resolved request.

## Non-Goals

This architecture does not by itself introduce:

1. a configuration-file format;
2. a complete provenance schema;
3. Intermediate → Book → EPUB rebuilding;
4. fully user-configurable Parser Grammar;
5. renderer layout configuration;
6. real-device typography tuning;
7. an EPUBCheck release-gate policy;
8. final JunkCleaner default-rule content;
9. automatic chapter renumbering;
10. generic semantic chapter inference;
11. global Arabic numeral conversion;
12. punctuation/sentence-length heuristics for paragraph splitting.

These remain separate decisions or future work.

## Acceptance Criteria

An implementation conforms to this architecture when:

1. CLI parsing is no longer the application-level configuration authority.
2. `ConversionRequest` is usable without importing or depending on `argparse`.
3. The Resolver can produce a `ConversionRequest` from CLI-independent configuration inputs.
4. Application defaults have a single authority.
5. `full_source` cross-field semantics are resolved centrally.
6. `ConversionRequest` contains no runtime component instances.
7. Execution does not mutate the resolved request.
8. Actual detected encoding does not overwrite the requested encoding policy.
9. Component-specific semantic validation remains owned by components.
10. Parser code does not need to understand CLI syntax.
11. Renderer code does not need to understand CLI syntax.
12. The existing Intermediate contract is not changed merely because the configuration model exists.
13. `ConversionRequest` is explicitly treated as resolved configuration/request, not as an execution plan.
14. Semantic groupings become dedicated types only when they carry meaningful responsibility, invariants, validation, or public API value.

## Final Architectural Statement

The V2.x Configuration Model establishes the following boundary:

```text
User Intent
    ↓
Configuration Resolution
    ↓
Resolved Application Request
    ↓
Execution
    ↓
Runtime Facts / Domain Results / Provenance
```

`ConversionRequest` is the resolved representation of user/application intent for one conversion operation.

It is not the CLI argument namespace, raw configuration, execution plan, execution context, runtime state, Book, or provenance record.

The CLI expresses the request. The Resolver determines its resolved meaning. `ConversionRequest` records that meaning. Execution performs the conversion. Runtime and provenance record what actually happened. `Book` records the resulting domain structure. EPUB is the final artifact.

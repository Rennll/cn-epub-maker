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

The current Python model is a frozen dataclass with these fields:

```text
ConversionRequest
├── source: Path
├── book_metadata: BookMetadata
├── destination: Path
└── policy: ConversionPolicy
    ├── encoding: str
    ├── parser: ParserPolicy
    │   └── paragraph_mode: str
    ├── transformations: TransformationPolicy
    │   ├── opencc: OpenCCConfig
    │   │   ├── enabled: bool
    │   │   └── profile: str
    │   ├── punctuation_enabled: bool
    │   └── junk_cleaner: JunkCleanerConfig
    │       └── rules: tuple[JunkRule, ...]
    └── full_source: bool
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

After resolution, `ConversionRequest` is logically immutable. The current implementation enforces this with `@dataclass(frozen=True)` on the request and its nested configuration dataclasses; the `JunkCleanerConfig.rules` collection is also represented as a tuple.

Execution reads the request but does not modify it. Runtime facts such as detected encoding remain local to execution/provenance rather than being written back into the request.

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

The actual detected encoding is a runtime/provenance value returned by input handling and retained by execution for reporting/audit purposes. It must not be written back into or mutate the `ConversionRequest`.

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
└── rules: tuple[JunkRule, ...]
```

The existing `JunkRule` already represents configuration data with `target`, `matcher`, and `pattern`. A separate `JunkRuleConfig` type is not required unless a future responsibility requires the separation of public schema from the current rule representation.

The central configuration model may carry `JunkCleanerConfig`, but it must not absorb JunkCleaner implementation semantics such as regex compilation, matching algorithms, block construction, or runtime state.

## Full Source Mode

`full_source` is a Conversion Policy / pipeline execution policy.

When `full_source = true`, the effective behavior is to bypass the transformation pipeline after Normalize. The current execution path passes this resolved policy into transformation orchestration, which produces no effective transformations in this mode.

Configuration resolution may therefore derive the effective transformation state as:

```text
full_source = true
        ↓
opencc.enabled = false
punctuation_enabled = false
junk_cleaner = empty effective rules
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

## Relationship to Application Architecture

The cross-version application pipeline and stage boundaries are defined in `architecture-overview.md`.

This document defines the configuration-specific contract at that boundary:

- CLI and configuration adapters provide configuration inputs;
- the Configuration Resolver determines application-level meaning and produces a `ConversionRequest`;
- execution consumes only the relevant resolved policy and data;
- runtime facts, domain results, and provenance remain outside the request.

`ConversionRequest` must not be passed through every stage as a generic configuration container.

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

## Anti-Patterns

The implementation must avoid the following:

### God Config

Do not create a configuration object that knows all component implementation details.

### Generic Config Passing

Do not pass the complete `ConversionRequest` into every stage merely because it is available. Stages should receive only the relevant policy/data.

### Configuration-owned Runtime Objects

Do not store transformer, parser, renderer, or other runtime instances inside configuration objects.

### Duplicate Application Defaults

Do not maintain competing application-default definitions in CLI parsing, configuration adapters, and the Resolver.

### Request Mutation

Do not mutate `ConversionRequest` with runtime facts such as detected encoding or execution results.

## Non-Goals

This document does not define:

- a complete configuration file format;
- the complete provenance schema;
- Intermediate → Book → EPUB rebuilding;
- fully user-configurable parser grammar;
- renderer layout configuration;
- real-device typography tuning;
- EPUBCheck as a release gate;
- final JunkCleaner default rules;
- automatic chapter renumbering;
- generic semantic chapter inference;
- global Arabic numeral conversion;
- punctuation/sentence-length paragraph heuristics.

These remain separate concerns or deferred decisions.

## Acceptance Criteria

The configuration architecture is considered coherent when:

- CLI syntax is not the application configuration contract;
- `ConversionRequest` is independent of `argparse.Namespace`;
- the Resolver can resolve from CLI-independent inputs;
- application defaults have one authoritative location;
- Full Source Mode semantics are resolved centrally;
- runtime instances do not live in the request;
- the request is not mutated during execution;
- actual encoding does not overwrite requested encoding;
- component-specific validation remains owned by components;
- parser and renderer do not need to know CLI syntax;
- the Intermediate contract is not changed merely to accommodate configuration;
- the request remains a request rather than an execution plan;
- stages consume relevant policy/data instead of a generic request container.

## Final Architectural Statement

The intended boundary is:

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

`ConversionRequest` is the resolved representation of application intent for one conversion operation.

It is not:

- a CLI namespace;
- raw configuration syntax;
- an execution plan;
- a generic execution context;
- runtime state;
- a `Book`;
- provenance.

The CLI expresses intent through frontend-specific syntax. Adapters remove that syntax. The Resolver determines application meaning. The request records that meaning. Execution performs the conversion. Runtime and provenance record what actually happened. The `Book` represents the resulting domain structure, and EPUB is the final artifact.

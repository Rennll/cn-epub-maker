# JunkRule Configuration Contract

## Status

This document is the canonical architecture and behavior contract for public `JunkRule` configuration in V2.x. It resolves DD-02 and defines the boundary between configuration input, rule validation, configuration resolution, and JunkCleaner execution.

Last updated: 2026-09-16 (initial)

The contract is intentionally narrower than a general configuration-file specification. It defines the rule model and semantics required for CLI and structured configuration support.

## Architectural Decision

Junk rules are configuration data that must be parsed, normalized, validated, and canonicalized before they enter the resolved `ConversionRequest`.

A dedicated configuration rule layer owns this work. It understands the public JunkRule schema and its rule semantics, but it does not execute transformations.

The execution layer receives validated canonical `JunkRule` entries and is responsible for applying them to text and reporting execution results.

The boundary is:

```text
CLI / Config / API input
        ↓
JunkRule configuration layer
  parse / normalize / validate / canonicalize
        ↓
canonical JunkRule[]
        ↓
Configuration Resolution
  defaults / precedence / cross-field semantics
        ↓
ConversionRequest
        ↓
Execution
        ↓
JunkCleaner
```

This is a rule-specific refinement of the general Configuration Model. It does not introduce another configuration precedence layer.

## Canonical Rule Model

The canonical model remains:

```text
JunkRule
├── target: "line" | "block"
├── matcher: "exact" | "contains" | "regex"
└── pattern: string
```

The existing typed `JunkRule` representation is retained. A second public `JunkRuleConfig` type is not introduced.

The canonical representation is independent of input source. CLI shorthand and structured configuration must produce equivalent `JunkRule` values.

## Public Input Forms

Two input forms are supported conceptually.

### Structured form

Structured configuration represents each rule as an object with the canonical fields:

```json
{
  "target": "line",
  "matcher": "regex",
  "pattern": "^廣告.*$"
}
```

A structured configuration contains an ordered collection of such rule objects.

### CLI shorthand

CLI exposes a repeatable shorthand using:

```text
TARGET:MATCHER:PATTERN
```

For example:

```text
line:contains:本章廣告
line:regex:^廣告.*$
block:exact:本文為贊助內容
```

The shorthand parser splits only the first two separators. The remainder is the pattern, so additional `:` characters belong to the pattern rather than changing its structure.

CLI syntax is an adapter concern. The canonical `JunkRule` model is not defined by the shorthand.

## Validation

Rule validation occurs before the rule can become part of an executable `ConversionRequest`.

The configuration rule layer validates:

- the rule is structurally valid;
- `target` is `line` or `block`;
- `matcher` is `exact`, `contains`, or `regex`;
- `pattern` is a string;
- when `matcher = regex`, the pattern is accepted by the supported Python regular-expression engine.

Invalid rules are configuration errors. They must not be silently skipped during normal conversion.

The configuration layer may compile a regex for validation. This compilation is validation work; the compiled regex is not stored in `ConversionRequest` and does not become runtime state.

At execution time, JunkCleaner compiles each canonical regex pattern as needed for matching. Execution may later introduce an explicit compiled-pattern cache as an optimization, but such a cache is runtime state and is not part of the configuration or request contract.

Execution may retain defensive invariant checks, but a known-invalid rule must not normally reach execution.

## Invalid Rule versus No Match

These states are deliberately different:

```text
Invalid rule
    → configuration error
    → no executable ConversionRequest
    → no conversion execution

Valid rule with zero matches
    → valid configuration
    → normal execution
    → matched = 0 / removed = 0
```

A valid rule not matching the current source is not an error.

## Configuration Precedence and Merge

The application configuration model remains:

```text
application_defaults < config_file < cli
```

`junk_rules` is an ordered collection and uses append semantics across explicit configuration sources:

```text
config rules + CLI rules
```

Configuration-file rules are retained in their declared order. CLI rules are appended in the order supplied on the command line.

This is intentionally different from scalar configuration values, where a higher-precedence source overrides a lower-precedence value.

If application defaults eventually provide built-in JunkRules, they participate as the lowest-order rule collection. Default-rule policy itself remains DD-03 and is not resolved by this document.

An unspecified source contributes no rules. An explicitly empty rule collection is distinct from an unspecified collection.

For JSON, the distinction is represented directly:

```json
{}
```

means `junk_rules` is unspecified, while:

```json
{
  "junk_rules": []
}
```

means the source explicitly supplies an empty rule collection. Under append semantics both contribute zero rules to the merged ordered collection, but the distinction remains observable to configuration handling and diagnostics and must not be collapsed implicitly.

## Ordering

Rule order is part of the transformation contract.

Rules are applied sequentially in their resolved order. No sorting, deduplication, or implicit grouping is performed by configuration resolution.

Therefore:

```text
config[0]
config[1]
CLI[0]
CLI[1]
```

resolves to the same execution order.

The configuration layer must preserve order through parsing, merging, and construction of `JunkCleanerConfig.rules`.

## Responsibility Boundaries

### Input adapters

Input adapters own source-specific syntax and transport concerns.

They may:

- parse CLI arguments into adapter values;
- load structured configuration data;
- preserve the source order of rules;
- pass raw rule entries to the rule configuration layer.

They must not:

- implement JunkCleaner matching;
- decide whether a regex matches text;
- silently drop malformed rules.

### JunkRule configuration layer

The rule configuration layer owns the public rule schema and rule-specific configuration semantics.

It may:

- parse supported rule representations;
- normalize representations into canonical `JunkRule` objects;
- validate rule fields;
- validate regex syntax;
- report configuration errors with rule/source context;
- preserve and merge rule order.

It must not:

- modify source text;
- instantiate or execute JunkCleaner;
- perform line/block matching against book content;
- generate EPUB output.

### Configuration Resolver

The Resolver owns application-level configuration semantics:

- defaults;
- source precedence;
- collection merge semantics;
- cross-field behavior such as Full Source Mode;
- construction of `ConversionRequest`.

The Resolver should not become a regex parser or JunkCleaner execution engine.

### JunkCleaner

JunkCleaner owns transformation execution:

- applying valid rules in order;
- counting matches/removals;
- producing transformation results and audit data;
- compiling regex patterns as needed for execution.

It does not interpret CLI shorthand or structured configuration syntax.

## Error Contract

Invalid rule configuration is fatal to configuration resolution for that conversion request.

The error should identify enough context for a caller to locate the offending rule, including its source when that information is available. Exact CLI wording and exception hierarchy are implementation details and must remain structured enough for frontends to present useful diagnostics.

A configuration error must occur before expensive conversion stages execute.

## Provenance

Rule input provenance is not part of `JunkRule` itself unless a future requirement makes provenance a stable domain property.

The current transformation audit may report execution statistics and warnings. The source of a configuration rule (for example, config file versus CLI) is configuration metadata, not a requirement to mutate the canonical rule or `ConversionRequest` with runtime state.

If future reproducibility requirements require preserving rule source/provenance, that should be introduced explicitly rather than by embedding frontend syntax in `JunkRule`.

## Full Source Mode

`full_source = true` retains its existing configuration semantics. The rule configuration layer validates all supplied rules first. An invalid rule remains a configuration error even when Full Source Mode will suppress all effective JunkCleaner execution. After successful validation, Full Source Mode resolves the effective JunkCleaner rule collection to empty.

Configuration validity and Full Source Mode suppression are separate concerns.

## Non-Goals

This decision does not define:

- the final built-in default JunkRule set;
- automatic semantic junk detection;
- source-specific rule profiles;
- fuzzy matching;
- replacement rules;
- rule priorities beyond declared order;
- regex flags or a custom regex engine;
- Intermediate schema changes;
- persistent rule provenance schema.

Those concerns require separate decisions if introduced.

## Acceptance Criteria

The following criteria apply to the DD-02 implementation milestone; they are not claims that this documentation PR alone satisfies them.

DD-02 is considered implemented when:

- structured rules and CLI shorthand produce the same canonical `JunkRule` model;
- invalid target, matcher, pattern shape, and regex syntax are rejected before execution;
- valid zero-match rules complete normally;
- config-file rules and CLI rules merge by append while preserving order;
- CLI adapter forwards the resolved rule input;
- `ConversionRequest` contains only canonical rule data, not compiled regex objects or frontend syntax;
- JunkCleaner no longer needs to interpret public input syntax;
- invalid configuration cannot produce a successful conversion with silently skipped rules;
- rule behavior is covered by unit and integration/regression tests.

## Decision Summary

DD-02 is resolved as:

```text
1C — structured canonical rules + CLI shorthand
2C — config rules + CLI rules, with CLI append
3B — invalid rules, including invalid regex, are configuration errors
```

The governing architectural principle is:

> Configuration owns understanding and validation of configuration data; execution owns applying already-valid instructions.

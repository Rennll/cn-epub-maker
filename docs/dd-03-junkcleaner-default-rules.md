# DD-03 — JunkCleaner Default Rules

## Status

Resolved.

## Decision

JunkCleaner has no built-in global default rules at the application level.

The effective application default for `junk_rules` is an empty ordered collection:

```text
application_defaults.junk_rules = ()
```

Existing behavior is therefore preserved: when no explicit JunkRule configuration is supplied, `JunkCleaner` performs no junk removal.

User-supplied rules remain supported through the DD-02 configuration contract. They are added through the existing configuration-source merge semantics and are not replaced by an implicit application rule set.

An explicitly empty `junk_rules` collection remains meaningful as configuration input, but it does not need to act as a switch for hidden built-in rules because there are no such global defaults.

## Rationale

The decision follows the DD-03 safety principle: a global default rule should require strong evidence that it identifies non-content material across the supported TXT input population, with a low risk of deleting legitimate正文.

The repository's existing fixtures provide negative evidence against broad semantic rules. URLs, mixed CJK/Latin text, chapter and volume headings, and other material that could superficially resemble metadata or promotion can occur as legitimate source content.

External TXT corpus inspection also found source-specific contamination such as repeated watermark text, fixed site footers, and patterns combining unusual repeated characters with a domain. These are plausible junk candidates, but their usefulness depends on the source that produced the TXT. Other observed material, including `广告`, copyright notices, ISBNs, publisher metadata, and URLs, can be legitimate content or book metadata and is therefore not safe as a global deletion rule.

Consequently, selecting a small collection of currently observed source-specific patterns as application-wide defaults would encode assumptions about particular TXT sources rather than establish a source-independent JunkCleaner contract.

## Rule Set

The built-in global default set is intentionally empty:

```text
[]
```

No default `exact`, `contains`, or `regex` JunkRule is introduced by this decision.

In particular, the following are not global defaults:

- generic URL matching;
- `广告`, `版权`, `作者`, `网站`, or similar keyword matching;
- generic QQ/group/contact matching;
- generic ISBN/publisher metadata matching;
- source-specific domain or footer strings observed in individual TXT corpora.

## Precedence and Explicit Configuration

DD-02 remains authoritative for rule configuration.

The application configuration model remains:

```text
application_defaults < config_file < cli
```

With no built-in rules, an omitted `junk_rules` value contributes an empty collection at the application-default layer. Explicit config-file and CLI rules are still merged by append in their declared order.

The distinction between an unspecified `junk_rules` value and an explicitly empty collection remains part of the configuration contract. The resolved effective rule collection is empty when neither source supplies rules, and it is also empty when all supplied rule collections are empty.

Full Source Mode keeps its existing semantics: supplied rules are validated first, then the effective JunkCleaner rule collection is suppressed to empty.

## Compatibility Impact

This decision does not intentionally change runtime behavior.

The current implementation constructs `JunkCleaner()` without built-in rules, and the resolver's application-default rule collection is empty. Resolving DD-03 therefore documents and freezes the existing behavior rather than introducing a new cleanup pass.

No runtime implementation change is required for DD-03 itself.

## Source-Specific Rules

Observed TXT contamination may justify source-specific rule sets in the future, but DD-03 does not introduce a source-profile mechanism.

A future requirement for source-aware defaults should be handled as a separate architectural decision rather than by silently expanding the global default set.

Likewise, an interactive or automated detection flow that proposes JunkRules from observed text is outside this decision. Candidate generation and user confirmation, if desired, should be specified independently from the global default-rule policy.

## Evidence

The decision was informed by:

- the existing `cn-epub-maker` JunkRule contract and regression fixtures;
- historical JunkCleaner behavior, which had no built-in default rules;
- inspection of public TXT corpora showing both genuine source contamination and legitimate metadata/content that would make broad keyword rules unsafe;
- external reader/conversion tooling that treats ad-cleaning rules as source-specific rather than universally safe.

These sources establish the absence of a sufficiently safe cross-source default set; they are not intended to define a new corpus-cleaning implementation.

## Reopen When

Reopen DD-03 only if there is evidence for a source-independent rule set with sufficiently low false-positive risk, or if the application introduces an explicit source-profile mechanism that changes the scope of what constitutes an application default.

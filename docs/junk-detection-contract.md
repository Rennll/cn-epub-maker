# Junk Detection Contract

Status: Semantic decisions frozen

## 1. Purpose

Junk Detection is an independent, read-only inspection workflow that helps users discover content with enough regularity to consider converting it into a `JunkRule`.

Its purpose is to reduce the cost of authoring JunkRules, not to delete content automatically.

Conceptual flow:

```text
source.txt
    ↓
inspect
    ↓
Detection Groups
    ↓
Suggested JunkRules
    ↓
Rule Preview
    ↓
user accepts / edits / skips
    ↓
output config
    ↓
normal build
    ↓
JunkCleaner
```

`inspect` does not modify the source or the user's existing configuration.

## 2. Responsibility Boundary

Junk Detection is responsible for:

- observing physical lines and blocks;
- finding repeated or otherwise regular content;
- applying limited, deterministic pattern abstraction;
- providing detection evidence;
- grouping related occurrences into Detection Groups;
- generating Suggested JunkRules;
- previewing Suggested JunkRules using canonical JunkRule matching semantics;
- letting the user accept, edit, or skip suggestions;
- writing accepted rules to a new config file.

Junk Detection is not responsible for:

- deleting source content;
- modifying `PhysicalDocument`;
- creating Chapter, Volume, Paragraph, or other semantic structures;
- deciding that content is definitely junk;
- modifying an existing user config;
- executing JunkCleaner;
- replacing Normalization;
- fuzzy or semantic interpretation.

Therefore:

> Detection ≠ Junk classification ≠ Removal.

## 3. Detection Scope

The first version observes only:

```text
line
block
```

`line` corresponds to `PhysicalLine` and `block` corresponds to `PhysicalBlock`.

A physical block is a contiguous non-blank run. Detection does not define semantic Paragraphs and must not split or merge physical structure merely for detection purposes.

Semantic Paragraph, Chapter, Volume, and related concepts remain Parser / Semantic Inference responsibilities.

## 4. Detection Group

A Detection Group is the user's decision unit. It represents a set of occurrences sharing a useful regularity rather than a single occurrence.

Conceptually:

```text
DetectionGroup
├── scope
├── pattern
├── occurrences
├── evidence
├── suggested_rule
└── rule_preview
```

For example:

```text
Pattern:
本章字數：<number>

Occurrences:
line 124
line 238
line 351
...

SuggestedRule:
line:regex:^本章字數：\d+$
```

A group does not necessarily map one-to-one to the final JunkRule.

## 5. Pattern

Pattern is a human-readable abstraction of a shared structure. It is not executable syntax.

Pattern and SuggestedRule are separate concepts:

```text
Pattern
    ↓
human-readable abstraction

SuggestedRule
    ↓
canonical executable JunkRule
```

Pattern must not be interpreted directly by JunkCleaner.

## 6. Pattern Abstraction

The first version permits only limited, deterministic variable abstraction.

Supported variable families may include:

- number;
- URL / domain;
- date / time using limited common formats;
- machine-like token / ID with a deterministic lexical shape.

The governing rule is:

> If a variable does not have a clear, deterministic lexical boundary, do not abstract it.

The first version does not perform:

- arbitrary `<text>` abstraction;
- semantic entity abstraction such as `<person>`;
- fuzzy matching;
- typo / edit-distance normalization;
- semantic similarity grouping;
- broad whitespace or punctuation normalization as part of detection.

A stable literal skeleton is required. Repetition alone is not enough to create a useful pattern.

## 7. Candidate Qualification

Candidate qualification does not use a simple occurrence-count threshold.

A candidate should have:

1. a stable literal skeleton;
2. deterministic abstraction for any variables;
3. a reasonable, narrow SuggestedRule;
4. enough supporting evidence to be useful to the user.

Supporting evidence may include occurrence count, distribution across the document, affected blocks, physical position, repetition consistency, and pattern specificity.

The core principle is:

> A candidate is shown not merely because it occurs often, but because it has enough regularity to be understandable and reasonably convertible into a narrow, verifiable JunkRule.

Internal ranking heuristics are allowed, but the first version does not require a public confidence score.

## 8. Detection Evidence

The first version uses four evidence families:

### Repetition

Repeated identical lines or blocks.

### Pattern

Different occurrences sharing a stable literal skeleton and deterministic variables.

### Boundary / Position

Repeated occurrence in similar physical context, such as a block start, block end, or other stable position.

### Format / Marker

Highly regular, isolated, footer-like, metadata-like, or marker-like formatting.

These are evidence sources, not Junk categories.

Detection may optionally describe a candidate as metadata, navigation, author note, advertisement, website residue, or unknown, but such classification does not itself make the content junk.

## 9. Suggested JunkRule

SuggestedRule uses the existing canonical public `JunkRule` model:

```text
JunkRule
├── target
├── matcher
└── pattern
```

For example:

```text
target = line
matcher = regex
pattern = ^本章字數：\d+$
```

A SuggestedRule is a recommendation, not yet configuration. It becomes a formal configuration rule only after the user accepts it or edits it into a valid rule.

Detection must not introduce a second executable rule language.

## 10. Rule Preview

A SuggestedRule must be validated and previewed against the inspected document before it is presented as actionable.

Preview must use the same canonical matching semantics used by the existing JunkRule / JunkCleaner implementation. Detection must not maintain a separate matching interpretation.

Conceptually:

```text
RulePreview
├── matched_count
├── affected_block_count
├── examples
└── locations
```

Detection Evidence answers:

> Why was this group detected?

Rule Preview answers:

> What will this actual JunkRule match?

If the SuggestedRule preview is substantially broader than the Detection Group, the inspection UI should warn the user so that the rule can be reviewed.

Preview is read-only and never performs removal.

## 11. User Decision Flow

The first interactive workflow uses a simple decision model:

```text
[a] accept
[e] edit
[s] skip
```

`accept` accepts the SuggestedRule.

`edit` allows the user to modify the rule. The edited rule must pass the existing JunkRule validation and must be previewed again.

`skip` rejects the suggestion without modifying the source.

Richer UI or non-interactive workflows may be added later without changing this core contract.

## 12. Output Config

Inspection outputs a new config file containing only accepted/final JunkRules.

Example:

```text
cn-epub-maker inspect novel.txt --output junk-config.toml
```

The generated config:

- contains accepted rules;
- contains user-edited accepted rules;
- excludes skipped candidates;
- excludes unaccepted suggestions;
- excludes detection evidence;
- excludes Rule Preview data;
- does not modify the existing config.

The generated config uses the existing public JunkRule configuration schema so it can be supplied to the normal build workflow.

## 13. Config Provenance / Audit

The formal JunkRule config remains clean and contains build behavior only.

Detection evidence, occurrence locations, pattern descriptions, preview results, acceptance history, and provenance are not stored in the first-version JunkRule config.

Audit / provenance reporting is an optional future feature. If needed, it can be implemented as a separate inspection report, for example:

```text
junk-config.toml
inspection-report.json
```

This keeps configuration and inspection history as separate concerns.

## 14. Config Interaction

Generated config participates in the existing configuration system. Existing precedence remains:

```text
application_defaults < config_file < cli
```

`junk_rules` retains its existing append semantics and ordering.

Detection does not redefine config precedence, rule validation, or JunkCleaner execution.

## 15. Safety Principle

The core safety principle is:

> Discover problems aggressively, modify conservatively.

More specifically:

```text
Detection
    can be broad

SuggestedRule
    must be narrow

Rule Preview
    must be verifiable

Removal
    only occurs through an accepted formal JunkRule
```

Unknown content is never removed merely because Detection found it. Removal occurs only after the user has explicitly accepted or authored the corresponding JunkRule and the normal build pipeline invokes JunkCleaner.

## 16. Architecture Boundary

Junk Detection is an independent inspection process rather than a mandatory stage of the normal build pipeline.

Normal build remains conceptually:

```text
Raw TXT
    ↓
Representation Normalization
    ↓
Content Transformations
    ├── JunkCleaner
    ├── OpenCC
    └── Punctuation
    ↓
Document Analysis
    ↓
Parser / Semantic Inference
    ↓
Intermediate
    ↓
Renderer
    ↓
EPUB
```

Inspection is a separate workflow:

```text
Raw TXT
    ↓
inspect
    ↓
Detection Groups
    ↓
Suggested JunkRules
    ↓
Rule Preview
    ↓
User Decision
    ↓
Generated Config
```

The generated config is then consumed by a normal build, where JunkCleaner performs the actual removal.

## 17. Non-Goals

The first version does not include:

- LLM or semantic AI interpretation;
- fuzzy matching;
- typo correction;
- arbitrary natural-language pattern abstraction;
- automatic junk deletion;
- automatic source rewriting;
- automatic chapter / volume inference;
- automatic paragraph inference;
- automatic chapter renumbering;
- broad whitespace normalization;
- broad punctuation normalization;
- source-specific built-in junk rules;
- persistent provenance inside JunkRule config;
- replacement rules;
- rule priority;
- regex flags beyond the existing canonical configuration contract.

## 18. Contract Summary

Junk Detection is a read-only, rule-authoring-oriented inspection workflow.

It observes physical source content, finds deterministic regularities, groups related occurrences, explains the evidence, proposes canonical JunkRules, previews their actual matching scope, and lets the user make the final decision.

The responsibility chain is:

```text
observe
  ↓
detect
  ↓
explain
  ↓
suggest
  ↓
preview
  ↓
user decides
  ↓
configure
  ↓
execute
```

It is deliberately not:

```text
detect
  ↓
guess
  ↓
delete
```

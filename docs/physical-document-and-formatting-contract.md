# Physical Document and Formatting Contracts

Status: Contract baseline

This document defines the physical-document, formatting-analysis, and parser boundaries used by `cn-epub-maker`. It is an implementation-independent contract. Implementations and tests SHOULD conform to these rules; this document SHOULD be updated before implementation behavior is intentionally changed.

## 1. Pipeline and ownership

The intended pipeline is:

```text
Raw TXT
  ↓
Representation Normalization
  ↓
Content Transformations
  ↓
Document Analysis
  ↓
Document Formatting Model
  ↓
Parser / Semantic Inference
  ↓
Intermediate Semantic Structure
  ↓
Renderer
  ↓
EPUB
```

The core ownership boundary is:

- Representation Normalization canonicalizes input representation. It MUST NOT perform semantic inference.
- Content Transformations may remove or modify unwanted content, subject to their explicit contracts.
- Document Analysis observes the post-transformation physical document and produces physical formatting evidence.
- The Document Formatting Model summarizes that evidence. It MUST NOT contain pre-classified semantic structure.
- The Parser interprets physical and formatting evidence into semantic structure.
- The Renderer chooses the output representation from semantic structure and MUST NOT re-interpret source whitespace as semantic structure.

### Analysis boundary

**Document Analysis MUST operate on the post-transformation text that will actually be passed to the Parser.**

Full Source Mode MAY skip content transformations, but MUST NOT bypass Document Analysis:

```text
read
 ↓
representation normalization
 ↓
skip content transformations
 ↓
Document Analysis
 ↓
Formatting Model
 ↓
Parser
```

### Transformation structural contract

**Content transformations may remove or modify unwanted content, but MUST NOT alter surviving physical structure unless that structural change is an explicit part of the transformation's contract.**

A content transformation that removes a Physical Block MAY change adjacent BlankLineRun topology as a direct consequence of removal, but MUST NOT silently reinterpret or collapse the resulting blank structure.

In particular:

```text
remove unwanted block
    ≠
normalize resulting blank structure
```

---

## 2. Physical Document Contract

**Physical Document is the ordered sequence of physical lines produced by representation normalization and content transformations, and consumed by Document Analysis and Parser.**

### Physical Line

A Physical Line is one element of the ordered physical document line sequence, delimited by a canonical LF line boundary or by the beginning/end of the document.

A Physical Line is not a visual line and is not a semantic Paragraph.

### Blank Physical Line

A Blank Physical Line is a physical line whose content consists entirely of whitespace characters under the canonical blank-line predicate.

The canonical blank-line predicate MUST be defined independently of paragraph or semantic interpretation.

Whitespace-only lines MAY include empty strings, ASCII whitespace, tabs, or ideographic whitespace, according to the canonical predicate.

Canonicalization of blank lines MUST NOT change the number or order of adjacent blank lines.

### Physical Block

A Physical Block is a maximal sequence of consecutive nonblank Physical Lines separated from adjacent Physical Blocks by one or more Blank Physical Lines.

A Physical Block is a physical grouping only. It MUST NOT be interpreted as a semantic Paragraph, Chapter, Heading, Quote, Scene Break, or other semantic document structure.

A Physical Block MUST NOT be interpreted as exactly one semantic Paragraph.

A semantic Paragraph MAY contain multiple Physical Lines.

### BlankLineRun

A BlankLineRun is a maximal sequence of consecutive Blank Physical Lines.

A BlankLineRun MUST preserve its exact observed length.

A BlankLineRun between two Physical Blocks MUST preserve its preceding and following block adjacency.

A leading or trailing BlankLineRun MAY have only one adjacent Physical Block.

A BlankLineRun MUST NOT contain a nonblank Physical Line.

BlankLineRun length MUST NOT itself assign semantic meaning.

### Shared physical-document invariant

Document Analysis and Parser MUST observe the same Physical Document.

Physical Document construction MUST be deterministic for the same normalized input and transformation configuration.

Document Analysis MUST NOT create evidence that cannot be traced to observable physical structure of the analyzed document.

---

## 3. Representation Normalization and whitespace

Representation Normalization is responsible for safe representation-level canonicalization such as:

- decoding the selected input encoding;
- removing an input BOM when appropriate;
- converting CRLF and CR line endings to LF.

Representation Normalization MUST NOT perform semantic inference.

Leading whitespace that can serve as formatting evidence MUST remain observable to Document Analysis and Parser. In particular, leading U+3000 MUST NOT be unconditionally removed during normalization merely because it resembles indentation.

Trailing whitespace is not a first-class Formatting Model pattern in v1. Its handling MUST nevertheless be explicit rather than being silently discarded inside Parser logic.

A stripped textual view MAY be derived for textual or semantic matching, but it MUST NOT replace the underlying Physical Line.

For example:

```text
raw physical line
    ├── whitespace-sensitive operations
    └── stripped textual view
             └── textual / semantic matching
```

**A stripped textual view MUST NOT silently become the source representation used for semantic output when source formatting is otherwise required to remain observable.**

---

## 4. Formatting Pattern Contract

### LeadingWhitespacePattern

**FormattingPattern describes observable leading-whitespace structure of a nonblank physical line.**

A LeadingWhitespacePattern MUST be derived only from nonblank Physical Lines.

Blank Physical Lines MUST be represented through BlankLineRun rather than LeadingWhitespacePattern.

Pattern identity MUST be independent of semantic interpretation and document-level frequency.

Distinct whitespace character types and counts MUST remain distinguishable when they constitute observable formatting evidence.

The conceptual v1 pattern forms are:

```text
NO_INDENT
ASCII_SPACES(n)
IDEOGRAPHIC_SPACES(n)
TABS(n)
MIXED
```

A serialized representation MAY use forms such as:

```text
NO_INDENT
ASCII_SPACE_x4
U+3000_x2
TAB_x1
```

`NO_INDENT` means that no leading whitespace was observed. It is not a semantic class and MUST NOT be treated as negative semantic evidence.

Patterns MUST NOT encode semantic meanings such as:

```text
PARAGRAPH_INDENT
HEADING_INDENT
QUOTE_INDENT
```

Observable leading-whitespace structure MUST remain available from the Physical Document passed to Document Analysis.

---

## 5. Document Analysis Contract

Document Analysis performs complete physical scanning and summarizes formatting evidence without assigning semantic document types.

It MAY observe:

- indentation / leading-whitespace patterns;
- blank-line runs;
- pattern frequency and context;
- formatting transitions;
- physical block composition;
- lightweight region or formatting-regime changes.

It MUST NOT perform semantic classification such as:

- Chapter;
- Heading;
- Paragraph;
- Scene Break;
- Quote;
- Separator meaning.

It MUST NOT encode rules such as:

```text
U+3000_x2 = paragraph
blank x5 = chapter
NO_INDENT = heading
```

It MUST NOT perform clustering or semantic understanding in the core v1 analysis model.

### Determinism

**Document Analysis MUST be deterministic for the same normalized, post-transformation physical document and analysis configuration.**

### Core output model

The core DocumentAnalysis model is:

```text
DocumentAnalysis
│
├── AnalysisMetadata
│     ├── physical_line_count
│     ├── nonblank_line_count
│     └── blank_line_count
│
├── PhysicalBlockEvidence[]
│     ├── block_index
│     ├── line_count
│     ├── first_format
│     └── last_format
│
├── BlankLineRunEvidence[]
│     ├── length
│     ├── preceding_block
│     └── following_block
│
├── FormattingPatternStatistics[]
│     ├── pattern
│     ├── total_count
│     ├── block_start_count
│     └── block_end_count
│
└── FormattingTransitionStatistics[]
      ├── from
      ├── to
      └── count
```

`FormattingRegime` is not part of the core model in v1. Lightweight regime detection MAY exist internally as analysis support, but it MUST NOT become semantic classification.

### PhysicalBlockEvidence

A PhysicalBlockEvidence MUST correspond to exactly one Physical Block in the post-transformation Physical Document.

A PhysicalBlockEvidence MUST describe physical structure only and MUST NOT assign semantic document types.

`line_count` MUST equal the number of nonblank Physical Lines in the corresponding block.

`first_format` and `last_format` MUST describe the observed LeadingWhitespacePattern of the corresponding first and last nonblank Physical Lines.

PhysicalBlockEvidence MUST NOT contain the block's full text.

Aggregate formatting statistics and transition frequencies SHOULD be represented at DocumentAnalysis scope rather than duplicated into every block.

### BlankLineRunEvidence

A BlankLineRunEvidence MUST correspond to exactly one BlankLineRun.

It MUST preserve the exact observed run length and, when applicable, references to the preceding and following Physical Blocks.

A leading or trailing BlankLineRun MAY have one missing adjacent block reference.

BlankLineRunEvidence MUST describe physical separation only and MUST NOT assign semantic meaning to run length.

The definition of a blank physical line MUST be consistent across transformations, analysis, and parsing.

### Formatting transitions

**A Formatting Transition is an observed change from one LeadingWhitespacePattern to another between two consecutive nonblank Physical Lines.**

Formatting transitions exist only within a Physical Block. They MUST NOT cross BlankLineRuns.

A FormattingTransitionStatistics identity is solely its `(from, to)` pair.

Self-transitions MUST be preserved.

Transition statistics MUST NOT assign semantic meaning to a transition.

**A FormattingTransition MUST NOT independently establish a semantic boundary.**

---

## 6. Parser ↔ Formatting Model Contract

The Parser consumes:

```text
Post-Transformation Physical Document
        +
Document Formatting Model
        +
Parser Configuration
```

The Formatting Model is contextual evidence, not a decision layer.

### Evidence, not decisions

**The Document Formatting Model MUST provide formatting evidence, not pre-classified semantic structure.**

The Formatting Model MUST NOT replace access to the Physical Document.

Parser MUST NOT independently reconstruct document-level formatting statistics already represented by the Formatting Model.

Parser MAY inspect local Physical Line, Physical Block, BlankLineRun, FormattingPattern, and FormattingTransition information as contextual evidence.

A FormattingPattern MUST NOT independently establish a semantic boundary.

A FormattingTransition MUST NOT independently establish a semantic boundary.

BlankLineRun length MUST NOT have universal semantic meaning.

Formatting evidence MAY materially influence semantic inference, but it MUST NOT independently establish semantic meaning.

### Paragraph modes

`wrapped` and `line` are Parser policies, not Document Analysis classifications.

In wrapped mode, when no higher-priority structural interpretation is sufficiently supported, the Parser MAY combine consecutive nonblank Physical Lines within a Physical Block into one semantic Paragraph.

In line mode, when no higher-priority structural interpretation is sufficiently supported, each ordinary nonblank Physical Line MAY become a semantic Paragraph.

A Physical Block MUST NOT be interpreted as exactly one semantic Paragraph.

A semantic Paragraph MAY contain multiple Physical Lines.

### Structural precedence

Heading and other higher-priority structural interpretations MUST be evaluated before paragraph inference.

A textual heading pattern MUST be evaluated in its structural context. An incidental textual match inside ordinary prose MUST NOT automatically establish a heading.

Higher-priority textual or structural interpretations MUST NOT be vetoed by lower-priority formatting evidence.

Global formatting frequency MUST NOT override stronger local textual or structural evidence.

Absence of a formatting pattern MUST NOT be treated as contradictory semantic evidence.

When multiple semantic interpretations satisfy their recognition criteria, the interpretation with higher semantic precedence MUST be preferred.

Parser MAY combine textual, physical, and formatting evidence when inferring semantic structure.

When no higher-priority interpretation is sufficiently supported, Parser SHOULD prefer the least-committal interpretation that preserves source content and physical structure.

Parser conflict resolution MUST be deterministic for the same Physical Document, Formatting Model, and Parser configuration.

---

## 7. Blank-run interpretation

The mapping from blank-run length to presentation or paragraph-boundary behavior is a default heuristic, not a universal semantic invariant.

For example, an implementation MAY currently use a policy equivalent to:

```text
1 blank line → NORMAL
2 blank lines → EXPANDED
3+ blank lines → SCENE_BREAK
```

but the contract MUST NOT claim that these lengths universally mean those semantic types.

BlankLineRun length MAY influence boundary presentation or heuristic weighting, but MUST NOT independently determine semantic boundary type.

---

## 8. Evidence conflict resolution and error priority

The parser SHOULD prioritize correctness in this order:

```text
Title / Chapter structure
    >
Major document structure
    >
Paragraph structure
    >
Whitespace fidelity
```

This is an error-priority policy, not a requirement to discard lower-level evidence whenever higher-level evidence exists.

The following principles apply:

1. Absence of evidence is not contradictory evidence.
2. Stronger local textual or structural evidence MUST NOT be overridden by global formatting frequency.
3. Formatting evidence MAY support, refine, or disambiguate semantic inference.
4. Formatting evidence MUST NOT independently establish semantic meaning.
5. When evidence is insufficient, over-classification SHOULD be avoided.
6. Source content and physical structure SHOULD be preserved whenever semantic interpretation is uncertain.

A small amount of ordinary paragraph misclassification MAY be preferable to losing or misclassifying a title or chapter boundary.

---

## 9. Renderer boundary

Renderer owns output representation.

Renderer MUST NOT re-interpret source whitespace as semantic document structure.

Source indentation does not imply that EPUB output must contain literal U+3000 characters. Equivalent presentation MAY be represented through CSS or another output-level mechanism when supported by the semantic model and renderer contract.

---

## 10. Implementation invariants

The following invariants SHOULD be covered by executable tests during implementation:

1. The same normalized, post-transformation Physical Document produces deterministic Document Analysis output.
2. Document Analysis and Parser observe the same Physical Document.
3. Leading U+3000 formatting evidence survives until Analysis and Parser.
4. Blank-line runs preserve their exact count and ordering unless an explicitly declared transformation changes that topology.
5. Whitespace-only lines use the same canonical blank-line predicate across transformation, analysis, and parsing.
6. Physical Blocks contain only consecutive nonblank Physical Lines.
7. BlankLineRuns contain only consecutive Blank Physical Lines.
8. Physical Blocks and BlankLineRuns do not independently acquire semantic types.
9. Formatting patterns distinguish observable whitespace character types and counts.
10. `NO_INDENT` does not act as negative semantic evidence.
11. Formatting transitions do not cross BlankLineRuns.
12. Formatting patterns and transitions do not independently establish semantic boundaries.
13. A Physical Block can produce multiple semantic Paragraphs.
14. A semantic Paragraph can contain multiple Physical Lines.
15. Global formatting frequency cannot override stronger local textual or structural evidence.
16. Incidental textual matches do not automatically become headings.
17. Full Source Mode still performs Document Analysis.
18. Parser conflict resolution is deterministic for identical input, model, and configuration.
19. Removing a Physical Block may change adjacent BlankLineRun topology as a direct consequence, but no separate blank-structure collapse occurs unless explicitly contracted.
20. Renderer does not re-infer source semantic structure from raw whitespace.

---

## 11. Non-goals for this contract

This document does not define:

- a universal novel-formatting classifier;
- a universal mapping from indentation to paragraph semantics;
- a universal mapping from blank-line count to chapter or scene-break semantics;
- source-specific rules for individual novels;
- clustering algorithms;
- confidence or likelihood scores for semantic classification;
- the final semantic AST shape;
- EPUB CSS or renderer-specific layout details.

Those decisions belong to later implementation or separate contracts.

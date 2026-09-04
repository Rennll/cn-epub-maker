# Architecture Overview

This document is the high-level map of the current system architecture. It describes the major stages, responsibilities, and boundaries of the pipeline without duplicating version-specific design decisions or implementation details.

## System Pipeline

The system transforms source text into a validated EPUB through these major stages:

```text
TXT
 │
 ▼
Normalize
 │
 ▼
Transformations
 │
 ▼
Parser
 │
 ▼
Intermediate
 │
 ▼
Renderer
 │
 ▼
EPUB
 │
 ▼
Validation
```

The exact transformation set and presentation semantics may evolve. This overview defines the architectural roles and boundaries rather than a fixed implementation sequence for every version.

The CLI is the orchestration layer around this pipeline. Conceptually it coordinates reading, normalization, transformation, parsing, model validation, optional Intermediate serialization, rendering, and EPUB validation; it does not own the semantics of those stages.

## Component Responsibilities

### Normalize

Normalize raw source text into a predictable input form before structural parsing or content transformation.

Normalization is responsible for input-level cleanup and representation consistency. It should not own book structure or EPUB presentation semantics.

### Transformations

Transform source content without owning the structural book model.

This stage contains content-oriented processing such as junk cleanup, script conversion, and punctuation conversion. Transformation behavior, ordering, configuration, and auditability are defined by the relevant transformation design documentation.

### Parser

Interpret normalized and transformed text as book structure.

The parser is responsible for identifying the structural hierarchy and paragraph-level source semantics needed by the book model. It should not perform presentation rendering or EPUB-specific formatting.

### Intermediate

Provide the stable structured representation exchanged between parsing, serialization, and later processing stages.

Intermediate preserves the information required to reconstruct the book while allowing the implementation to serialize, inspect, and process the structured result independently of the original source text.

### Renderer

Convert the structured book representation into the publication representation used to build the EPUB.

The renderer owns output semantics such as semantic HTML structure, paragraph presentation classes, hard line-break representation, and chapter pagination intent. It should not infer or silently rewrite source semantics owned by the parser or Intermediate model.

The current Pandoc-based renderer uses Pandoc to convert chapter content from the project's intermediate Markdown form to HTML fragments, then applies project-specific semantic post-processing before EPUB assembly. Pandoc is therefore a rendering backend, not the owner of the complete EPUB package.

### EPUB Generation

Package rendered content and supporting resources into the final EPUB artifact.

EPUB generation is an output concern. It consumes renderer output and assembles the package-level resources and relationships required by the project, rather than reimplementing parsing, transformation, or book-structure decisions.

### Validation

Verify that generated output satisfies the project's required structural and packaging guarantees.

Validation has three conceptual layers:

1. **Book/model validation:** check the structured `Book` result before rendering, including required metadata and chapter presence.
2. **EPUB structural validation:** inspect the generated ZIP/package relationships, including `mimetype`, container, OPF, manifest, spine, navigation, and referenced targets.
3. **EPUBCheck:** optionally run the external EPUBCheck tool for additional standards validation.

The first two layers are built into the project. EPUBCheck is an optional external dependency; when it is unavailable, built-in structural validation can still determine whether the generated package satisfies the project's own structural guarantees.

Validation checks produced results rather than defining upstream semantics.

## Architectural Boundaries

The main boundaries are:

- **Input boundary:** Normalize isolates raw source irregularities from later stages.
- **Content boundary:** Transformations modify content while remaining separate from structural interpretation.
- **Structure boundary:** Parser and Intermediate establish and preserve the book model.
- **Presentation boundary:** Renderer turns structure into publication-oriented output without redefining upstream semantics.
- **Artifact boundary:** EPUB generation packages the rendered result.
- **Verification boundary:** Validation checks the final artifact independently of how it was produced.

These boundaries are intended to keep responsibilities explicit and make changes local to the stage that owns them.

## Relationship to Version-Specific Design Documents

This document answers:

> What are the major parts of the system, what does each part own, and how do they connect?

Version- and subject-specific design documents answer different questions:

- `v1-architecture-decisions.md` records the stable V1 structural and EPUB decisions.
- `v2-migration-and-design-decisions.md` records V2 transformation/integration decisions, migration boundaries, and related constraints.
- `v2x-typography-and-layout.md` records V2.1 typography and layout semantics and presentation constraints.

Those documents should extend or refine this architecture map rather than reproduce the entire pipeline.

## Stability and Scope

This overview is intentionally high level. It should change only when the system's major responsibilities, boundaries, or data flow change.

Detailed behavior belongs in the appropriate canonical design document, source code, tests, or repository configuration. Historical implementation chronology belongs primarily in Git history, pull requests, and issue discussions.

The overview does not define every current implementation detail and should not be treated as a substitute for component-specific contracts.

# Architecture Overview

This document is the high-level map of the current system architecture. It describes the major stages, responsibilities, boundaries, and architectural evolution without duplicating version-specific design decisions or implementation details.

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

## Architectural Evolution

The project evolved by extending a stable structural pipeline rather than replacing it at each version boundary.

### V1 — Structural and EPUB baseline

V1 established the core domain and output boundaries:

```text
source text
  ↓
Normalize → Parser → Book → Intermediate → Renderer → EPUB → Validation
```

Its key architectural commitments are conservative structural parsing, preservation of source structure, a stable `Book` model, an Intermediate serialization boundary, and Pandoc-first EPUB rendering with project-owned package assembly and validation.

V1 is the baseline that later versions extend. It does not include semantic content transformation or heuristic structural rewriting.

### V2 — Transformation and integration layer

V2 extends the V1 structural core rather than redefining it:

```text
Normalize → Transformations → Parser → Book → Intermediate → Renderer → EPUB
               │
               ├─ Junk Cleaner
               ├─ OpenCC
               └─ Punctuation Conversion
```

V2 introduced isolated content transformations, transformation ordering and auditability, Full Source Mode, and application/CLI integration. The `Book`, Intermediate, parser, and Pandoc-first renderer remain the structural foundation.

### V2.x — Application and presentation refinement

V2.x refines the surrounding contracts without replacing the V1/V2 core. The main additions are:

- an application-level `ConversionRequest` and typed policy model;
- a configuration adapter/resolver boundary between frontends and execution;
- explicit separation of configuration, runtime state, and provenance;
- typography/layout semantics at the renderer boundary;
- future-facing presentation and book-level extension points that remain separate from the core content model.

V2.x is an evolution path, not a second pipeline. Version labels identify milestones or subject areas; they do not imply a new architecture for every version.

Detailed contracts remain in the relevant design documents:

- `v1-architecture-decisions.md` — V1-specific structural, parsing, Intermediate, EPUB, and non-goal decisions;
- `v2-migration-and-design-decisions.md` — V2 transformation, migration, integration, and compatibility decisions;
- `v2x-configuration-model.md` — V2.x application configuration and execution-boundary contract;
- `v2x-typography-and-layout.md` — V2.x typography and layout semantics.

These documents should refine the architecture map rather than restate the complete pipeline or duplicate each other's responsibilities.

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

Provide the structured representation exchanged between parsing, serialization, and later processing stages.

Intermediate preserves the information required to reconstruct the book while allowing the implementation to serialize, inspect, and process the structured result independently of the original source text. Its semantic contract and any future rebuildability are documented separately.

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

## Application Boundary

V2.x makes the application-level configuration boundary explicit without changing the underlying content pipeline:

```text
CLI / Config File / API
        ↓
CLI / Configuration Adapter
        ↓
Configuration Resolver
        ↓
ConversionRequest
        ↓
Application Execution
        ├── Input / Decode
        ├── Normalize
        ├── Transform
        ├── Parser
        ├── Validation
        ├── Intermediate
        ├── Renderer
        └── EPUB Validation
```

`ConversionRequest` describes one resolved conversion operation. It is not an execution plan, runtime context, `Book`, or provenance record. Runtime facts such as actual encoding and transformation audit data remain outside the request model.

The application passes only the relevant policy or data to each stage rather than treating `ConversionRequest` as a generic container. Detailed configuration fields, precedence, and validation responsibilities belong to `v2x-configuration-model.md`.

## Architectural Boundaries

The main boundaries are:

- **Input boundary:** Normalize isolates raw source irregularities from later stages.
- **Content boundary:** Transformations modify content while remaining separate from structural interpretation.
- **Structure boundary:** Parser and Intermediate establish and preserve the book model.
- **Presentation boundary:** Renderer turns structure into publication-oriented output without redefining upstream semantics.
- **Artifact boundary:** EPUB generation packages the rendered result.
- **Verification boundary:** Validation checks the final artifact independently of how it was produced.
- **Application boundary:** Configuration resolution converts frontend-specific input into a stable application request without becoming part of the domain model or runtime state.

These boundaries are intended to keep responsibilities explicit and make changes local to the stage that owns them.

## Stability and Scope

This overview should change when the system's major responsibilities, boundaries, data flow, or version evolution materially change. It should not change merely because an implementation detail changes.

Detailed behavior belongs in the appropriate canonical design document, source code, tests, or repository configuration. Historical implementation chronology belongs primarily in Git history, pull requests, and issue discussions.

The overview is the canonical high-level architecture map. It does not define every component-level contract and should not be used as a substitute for the detailed design documents.

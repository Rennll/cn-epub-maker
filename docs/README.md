# Documentation Map

This directory contains the project's durable design knowledge and lightweight session context.

Documentation is organized by information responsibility and subject, not strictly by version number. Version labels describe project evolution and contracts, but they do not by themselves determine where information belongs.

## Documentation Policy

Project documentation should preserve information that is useful for future implementation, review, or architectural reasoning and cannot be reliably reconstructed from source code, tests, or repository configuration.

Documentation should describe requirements, contracts, constraints, decisions, and important rationale rather than duplicate implementation details.

Each durable piece of project knowledge should have one canonical source. Other documents may reference that source but should not maintain a separate copy of the same information.

When information changes responsibility or becomes part of a more stable contract, move or update it in the appropriate canonical document instead of continuing to accumulate it in a session note or historical document.

Source code and tests are the canonical source for implemented behavior. Documentation is the canonical source for durable intent, requirements, constraints, and design rationale. These sources answer different questions and may temporarily differ; a conflict should be made explicit and resolved rather than hidden by choosing one source as universally higher priority.

## Information Retention Rules

### Keep

Keep information when it has durable value and affects future work, especially:

- confirmed project requirements and behavioral contracts;
- architectural decisions and important rationale;
- explicit constraints and non-goals that prevent incorrect future implementations;
- stable boundaries between components or pipeline stages;
- migration decisions explaining why legacy behavior is retained, changed, or rejected;
- design decisions that span multiple implementation changes or versions;
- compatibility requirements that cannot be reliably inferred from code alone.

Completed work may remain documented when it defines a stable contract or explains an architectural boundary. Completion status is not a reason by itself to delete durable knowledge.

### Do Not Duplicate

Do not copy information into documentation when it can be reliably derived from:

- source code;
- tests;
- CI configuration;
- generated artifacts;
- Git history, pull requests, or issue discussions.

Documentation may summarize these sources when the summary provides architectural context or rationale, but it should not become a second implementation specification.

Do not repeat the same requirement across multiple canonical documents merely to associate it with different versions. Prefer one authoritative description and reference it from related documents.

### Session Context

`next-session-handoff.md` is temporary continuation state.

It should contain only information needed to decide what to work on next and information that cannot be reliably derived from the repository.

A handoff should normally contain:

- the next concrete focus;
- unresolved questions or decisions requiring follow-up;
- important constraints that are not obvious from the repository.

It should not contain a copy of the project's architecture, completed milestones, implementation details, or established design decisions already documented elsewhere.

When a temporary observation becomes a durable requirement or architectural decision, move that knowledge into the appropriate canonical document. When the session work is complete, replace obsolete handoff state rather than accumulating it as project history.

Session-specific preferences, temporary instructions, and observations should not become permanent project requirements unless they are explicitly established as such.

### Historical Information

Development history belongs primarily in Git commits, pull requests, and issue discussions.

A historical document is justified only when the history itself explains a durable design decision, migration boundary, compatibility constraint, or other information that future maintainers would otherwise have difficulty reconstructing.

Do not preserve session history merely for completeness.

## Document Map

### Architecture Overview

`architecture-overview.md`

Canonical high-level map of the current system architecture, including major pipeline stages, component responsibilities, cross-stage boundaries, orchestration, and validation layers.

Use this document to understand how the system fits together. Keep version- or component-specific behavioral contracts in their respective canonical documents.

### V1 Architecture

`v1-architecture-decisions.md`

Canonical description of the stable V1 architecture and behavioral contract.

Use this document for durable V1 decisions involving the core data model, parsing behavior, Intermediate boundary, EPUB generation, validation, and V1 non-goals.

It should describe the stable contract rather than the chronological history of V1 development.

### V2 Transformation and Integration

`v2-migration-and-design-decisions.md`

Canonical description of the completed V2 transformation and integration architecture.

Use this document for durable decisions concerning transformations, transformation ordering, configuration, CLI orchestration, audit metadata, migration decisions, and the boundaries between V1 and V2.

V2 documentation should not duplicate the implementation details of individual transformers when those details are already represented by source code and tests.

### V2.1 Typography / Layout

`v2x-typography-and-layout.md`

Canonical description of the V2.1 typography and layout semantics.

Use this document for paragraph-boundary semantics, hard line breaks, semantic rendering, chapter pagination intent, typography/layout responsibilities, and related presentation constraints.

V2.1 is a project milestone within the broader V2.x evolution path. Its documentation is kept separately because typography/layout forms a coherent design concern, not simply because it has a different version number.

### Current Session

`next-session-handoff.md`

Temporary continuation note for the next implementation session.

Keep this file short and replace obsolete content as the current task changes. It is not a canonical architecture document and should not become a project history log.

## Version and Subject Boundaries

The project uses version labels to describe architectural evolution, but version boundaries and documentation boundaries are not identical.

V1 is the stable structural and EPUB-generation baseline.

V2 is the completed transformation and integration stage built on top of V1.

V2.1 is the typography/layout milestone within the broader V2.x evolution.

Future V2.x work may introduce new capabilities or revise completed architecture. Such work should receive its own canonical documentation when it establishes a durable contract, but it does not automatically require a new version-wide document.

When a subject crosses version boundaries, prefer documenting the subject in the place that provides the clearest canonical source rather than duplicating it into every affected version document.

## Handling Conflicts

Requirements and decisions describe what the project intends to do. Source code and tests describe what the project currently does.

If they disagree, do not treat either side as universally higher priority. Identify the difference and decide whether the requirement/documentation or the implementation should change.

Once the difference is resolved, update the relevant canonical source and tests so that the intended contract and implemented behavior are clear and consistent.

Temporary session notes and historical discussions may provide context for the discrepancy, but they are not a substitute for resolving it.

## Maintenance Principles

Keep documentation small enough to remain trustworthy.

Prefer updating an existing canonical document over creating a new document for a small addition.

Create a new document when a subject has enough independent requirements, decisions, or constraints to justify its own stable source of truth.

Do not create documents solely to mirror version numbers.

When a document no longer has a distinct responsibility, consolidate or remove it rather than maintaining overlapping sources of truth.

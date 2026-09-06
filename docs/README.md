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

Do not create a version-wide architecture document merely because a new version label exists. Put cross-version architecture in `architecture-overview.md`; keep a version-specific document only when it contains decisions, contracts, migration constraints, or other detail that cannot be cleanly represented in the overview.

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

Canonical high-level map of the current system architecture and its V1 → V2 → V2.x evolution, including major pipeline stages, component responsibilities, cross-stage boundaries, application orchestration, and validation layers.

Use this document to understand how the system fits together. Keep version- or component-specific behavioral contracts in their respective canonical documents.

### V1 Structural Decisions

`v1-architecture-decisions.md`

Canonical V1-specific decisions and stable behavioral contracts, including parsing semantics, Intermediate details, EPUB guarantees, and V1 non-goals.

It should not duplicate the overall V1 architecture map already documented in `architecture-overview.md`.

### V2 Transformation and Integration

`v2-migration-and-design-decisions.md`

Canonical V2-specific transformation contracts, migration decisions, integration boundaries, and compatibility constraints.

It should not duplicate the overall V2 architecture map already documented in `architecture-overview.md`.

### V2.x Configuration

`v2x-configuration-model.md`

Canonical V2.x application configuration and execution-boundary contract, including `ConversionRequest`, policy objects, resolution, validation, and separation of configuration from runtime state and provenance.

### V2.x Typography / Layout

`v2x-typography-and-layout.md`

Canonical V2.x typography and layout semantics, including paragraph-boundary semantics, hard line breaks, semantic rendering, chapter pagination intent, and presentation constraints.

### Decision Register

`deferred-decision-audit.md`

Decision register for open, partially resolved, resolved, and frozen architectural or behavioral questions. It records current status and points to the canonical source; it is not an architecture document or implementation task list.

### Future Directions

`future-directions.md`

Canonical record of deliberately deferred architecture directions and capabilities that are not part of the current implementation contract.

### Audits

`audits/`

Historical maintenance, provenance, and licensing records. These are retained when the history itself is durable project knowledge and should not be treated as current architecture documentation.

### Current Session

`next-session-handoff.md`

Temporary continuation note for the next implementation session.

Keep this file short and replace obsolete content as the current task changes. It is not a canonical architecture document and should not become a project history log.

## Version and Subject Boundaries

The project uses version labels to describe architectural evolution, but version boundaries and documentation boundaries are not identical.

V1 established the stable structural and EPUB-generation baseline.

V2 extended that baseline with isolated content transformations and application integration without replacing the V1 structural model, Intermediate boundary, or renderer foundation.

V2.x continues the same architecture by refining application configuration, execution boundaries, and presentation semantics. It is an evolution path rather than a separate architecture.

When a subject crosses version boundaries, prefer documenting the architecture in `architecture-overview.md` and the detailed contract in the document that owns that subject. Do not duplicate the same architecture merely to associate it with a version label.

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

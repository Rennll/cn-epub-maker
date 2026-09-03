# Documentation Map

This directory is primarily for AI/session context rather than the human-facing project introduction.

## Canonical Documents

### V1

`v1-architecture-decisions.md`

The stable V1 architecture and behavioral contract. Use this when reasoning about the completed V1 system.

### V2

`v2-migration-and-design-decisions.md`

The V2 architecture, migration decisions, and implementation boundary. V2 extends the completed V1 core with the transformation pipeline and its CLI/Intermediate integration.

### Current Session

`next-session-handoff.md`

Temporary continuation state for the next unfinished task. It should stay short and current. Information that becomes a stable architectural fact or decision should move into the appropriate canonical document instead of accumulating here.

## Version Boundaries

V1 is the stable baseline. V2 is the completed transformation and integration stage built on top of that baseline. V2.x is reserved for subsequent architectural or feature evolution that requires a new contract, such as rebuilding the `Intermediate → Book → EPUB` path.

## Information Boundaries

Use the repository source code and tests as the canonical source for implementation details. Do not duplicate implementation facts in these documents when they can be inspected directly.

Use V1 documentation for the completed V1 contract, V2 documentation for the completed V2 architecture and confirmed design decisions, and the handoff only for current unfinished work and session-specific context.

Historical handoff documents are not canonical project documentation. Once their durable knowledge has been incorporated into V1 or V2, their remaining session state can be discarded.

# Documentation Map

This directory is primarily for AI/session context rather than the human-facing project introduction.

## Canonical Documents

### V1

`v1-architecture-decisions.md`

The stable V1 architecture and behavioral contract. Use this when reasoning about what the completed V1 system is supposed to do.

### V2

`v2-migration-and-design-decisions.md`

The current V2 design and migration decisions. The first V2 transformation slice is now implemented and validated end-to-end; the document remains the architectural baseline for the remaining V2 work.

### Current Session

`next-session-handoff.md`

Temporary continuation state for unfinished work. It should stay short and current. Information that becomes a stable architectural fact or decision should move into the appropriate canonical document instead of accumulating here.

## Information Boundaries

Use the repository source code and tests as the canonical source for implementation details. Do not duplicate implementation facts in these documents when they can be inspected directly.

Use V1 documentation for completed architecture and behavior, V2 documentation for confirmed future design decisions and the current V2 implementation boundary, and the handoff only for current unfinished work and session-specific context.

Historical handoff documents are not canonical project documentation. Once their durable knowledge has been incorporated into V1 or V2, their remaining session state can be discarded.

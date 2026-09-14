# Next Session Handoff

## Current Context

The V2.x architecture refactor is complete.

The project is now in the validation and release-correctness phase. Focus on verifying existing contracts in real EPUB output and resolving remaining operational decisions.

GitHub Issues are the authoritative work queue. Do not duplicate the issue backlog or create a second roadmap here.

## Implementation Queue Rules

1. Inspect the current open GitHub Issues before choosing work.
2. Work from the highest-priority unblocked issue.
3. Do not work on an issue marked `status:blocked` while any issue in its `Blocked by` section remains incomplete.
4. If multiple unblocked issues have the same priority, prefer the issue that is upstream in the dependency chain.
5. Read the issue body, its direct dependencies, and referenced canonical docs before implementation.
6. Use Issue state as completion state. Do not create `status:ready`, `status:in-progress`, or `status:done` labels as a second state system.
7. Keep dependency metadata in the issue body using the `## Dependencies` / `### Blocked by` / `### Blocking` convention. Record only direct dependencies.
8. After implementation, run focused tests and relevant end-to-end regression tests before closing the issue.
9. When a blocker is closed, remove `status:blocked` from issues that are now unblocked and keep their dependency sections accurate.
10. Update canonical documentation only when a stable contract or decision changes.

## Current Priority Chain

The current intended implementation order is:

```text
#34  P0 architecture
 ↓
#29  P0 runtime
 ├──→ #35  P1 encoding policy
 ├──→ #36  P1 output policy
 │     ↓
 │    #33  P2 filename implementation
 └──→ #32  P1 configuration resolver

#34  also blocks #31 (P1 intermediate schema)
```

Parser-specific and validation work should not be artificially blocked unless the issue itself establishes a direct dependency.

## Session Guidance

When starting a new session:

1. Inspect the current open GitHub Issues before choosing work.
2. Check `docs/deferred-decision-audit.md` when an issue involves an unresolved design decision.
3. Read the issue's dependency metadata before implementation.
4. Preserve current architecture boundaries and non-goals unless new evidence or requirements justify reopening them.

## Handoff Notes

Use this section only for session-specific context that cannot be recovered from the repository, GitHub Issues, or decision register.

Currently: none.

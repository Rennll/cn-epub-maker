# DD-08 EPUBCheck Validation Policy

## Status

Resolved.

## Decision

EPUBCheck is an external conformance validation layer. It complements, rather than replaces, the project's built-in EPUB structural validation.

### `build`

Normal local builds always run built-in EPUB validation. They do not require EPUBCheck and do not invoke EPUBCheck automatically.

A successful build therefore means that the built-in validation passed; it does not claim full EPUBCheck conformance.

### `validate`

`novel-epub validate <epub>` always runs built-in EPUB validation first. It then runs EPUBCheck when the executable is available.

If EPUBCheck is unavailable in this optional mode, validation remains successful and emits a deterministic warning:

`EPUBCheck executable not found; external validation skipped.`

If EPUBCheck is available and reports a non-zero exit status, validation fails.

The `--require-epubcheck` option makes EPUBCheck availability mandatory. In this mode, a missing executable and any EPUBCheck validation failure both return exit code 1.

### `CI`

CI must provide EPUBCheck explicitly and run the strict validation path. Missing EPUBCheck is therefore a CI failure rather than a silently skipped check.

The CI environment pins the EPUBCheck release used by the project so that validation behavior is reproducible.

### `release`

EPUBCheck is a release gate. A release must not proceed when EPUBCheck is unavailable or reports a validation failure.

Release automation should invoke the same strict validation path used by CI rather than maintaining a separate validation implementation.

## Exit semantics

- `0`: validation succeeded under the selected policy.
- `1`: built-in validation failed, EPUBCheck failed, or required EPUBCheck was unavailable.

The existing build-specific execution codes remain unchanged: book validation failure is `2`, and built-in EPUB validation failure is `3`.

## Missing-tool behavior

Optional validation treats a missing EPUBCheck executable as a warning. Required validation treats the same condition as an error. This distinction is explicit in the validator API through the `required` argument and in the CLI through `--require-epubcheck`.

## Scope boundary

This decision does not make EPUBCheck part of normal conversion execution, does not replace built-in structural validation, and does not define reader/device rendering compatibility. Real reading-environment validation remains covered by DD-07.

## Reference

The current production-ready EPUBCheck release is 5.3.0. The project should update the pinned CI/release version deliberately rather than tracking an unpinned `latest` download.

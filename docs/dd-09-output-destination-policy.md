# DD-09 — Output Destination and Filename Policy

## Status

Resolved.

This document is the canonical behavioral policy for output destination selection, automatically generated filenames, filename sanitization, collision handling, and parent-directory behavior.

The `deferred-decision-audit.md` records that DD-09 is resolved and points here for the detailed contract. `v2x-configuration-model.md` defines the application configuration/request architecture; it does not duplicate the filesystem behavior defined here. Runtime and CLI components implement this policy at their respective boundaries.

## 1. Destination modes

There are two distinct destination modes:

1. **Automatic destination** — no `destination` is supplied by the user. The application derives a filename from request metadata and places it beside the source file.
2. **Explicit destination** — the user supplies `destination`. The supplied path is preserved as the requested destination and is not rewritten by metadata filename sanitization.

The distinction must remain available to the execution/output layer because automatic destinations may be sanitized and collision-resolved, while explicit destinations are never silently changed.

## 2. Automatic filename derivation

The initial automatic filename is:

```text
<title>_<author>.epub
```

The title and author come from resolved `BookMetadata`.

The initial name is a logical filename only. It must pass through the sanitization rules below before being used as a filesystem path.

The automatic destination directory is the source file's parent directory. The application does not create an additional parent directory for an automatically generated destination.

## 3. Filename sanitization

Sanitization applies only to automatically generated filenames, never to an explicit destination path.

The following path-sensitive or platform-invalid ASCII characters are replaced with their full-width Unicode equivalents when the replacement is safe and meaningful:

| Input | Replacement |
| --- | --- |
| `/` | `／` |
| `\\` | `＼` |
| `:` | `：` |
| `*` | `＊` |
| `?` | `？` |
| `"` | `＂` |
| `<` | `＜` |
| `>` | `＞` |
| `|` | `｜` |

ASCII control characters are removed. Characters that cannot safely be represented in a supported filename and have no defined safe replacement are removed rather than causing conversion to fail.

Path separators are therefore treated as filename content during automatic name generation; they must never create additional path components.

After character replacement/removal:

- leading and trailing ASCII whitespace is removed;
- leading and trailing `.` characters are removed;
- repeated whitespace inside the filename is preserved unless required for filesystem safety;
- the `.epub` extension is applied after sanitization and is not itself sanitized;
- the resulting filename must not be `.` or `..` or otherwise empty.

The sanitization policy is intentionally conservative: preserving useful metadata is preferred, but filesystem safety takes precedence.

## 4. Reserved and unusable names

Windows-reserved device names are treated as unusable for automatically generated filenames, including the case where the reserved name is followed by an extension. The comparison is case-insensitive and ignores a trailing sequence of spaces or periods for the purpose of the reserved-name check.

If sanitization produces an empty, `.`/`..`, or otherwise unusable stem, the deterministic fallback stem is:

```text
book
```

The final fallback filename is therefore `book.epub` before collision handling.

## 5. Collision handling

The application must never overwrite an existing EPUB by default.

For an automatically generated destination, if the candidate already exists, select the first available deterministic suffix:

```text
book.epub
book (01).epub
book (02).epub
...
```

The same suffix scheme applies to any sanitized metadata-derived stem.

Collision selection must happen immediately before output creation so that the selected path reflects the filesystem state at execution time. The output creation step must preserve the same non-overwrite guarantee if another process creates the selected path between collision selection and creation; the exact filesystem API used to achieve that guarantee is an implementation detail.

No `--force` or overwrite option is introduced by DD-09.

## 6. Explicit destinations

An explicitly supplied destination is not sanitized or renamed according to metadata rules.

The application must not silently replace path separators, reserved names, whitespace, or other characters in an explicit destination. If the explicit path is invalid or cannot be used, conversion fails with an execution/output error rather than silently choosing another path.

An existing explicit destination is also not automatically renamed to a collision suffix. Because the user explicitly selected the destination, the default policy is to fail rather than overwrite or silently redirect it.

## 7. Parent directories

The application does not implicitly create missing parent directories for either destination mode.

- An automatically generated destination uses the existing source parent directory.
- An explicit destination must refer to an existing or otherwise writable parent directory.
- A missing or unusable parent directory is an execution/output error.

This keeps filesystem mutation limited to the requested output artifact and avoids silently creating directory trees as a side effect of conversion.

## 8. Reporting and provenance

When automatic sanitization changes the initial metadata-derived filename, the execution/reporting layer must expose that fact to the user rather than hiding it.

When collision handling changes the candidate name, that fact must likewise be reported.

The actual output path belongs in `ExecutionResult.epub_path`. The originally derived name and the selected actual path are runtime/output facts and must not be written back into `ConversionRequest`.

A warning is the default user-visible reporting mechanism for automatic filename changes. The warning should distinguish at least:

- metadata-derived name changed by sanitization; and
- candidate changed because of an existing-file collision.

## 9. Document boundaries and scope

DD-09 defines destination semantics. It does not define:

- the Python shape of `ConversionRequest` or `ConversionPolicy`;
- CLI/config-file syntax for expressing `destination`;
- a user-facing overwrite/force option;
- EPUBCheck behavior;
- reader-specific EPUB compatibility;
- renderer-specific output naming behavior.

The configuration architecture owns the request model; DD-09 owns the behavioral meaning of destination handling. The runtime/output implementation owns the concrete filesystem operations. These layers should reference this policy rather than independently redefining the rules.

The implementation child **#33** should apply this policy without introducing additional product-level filename decisions.

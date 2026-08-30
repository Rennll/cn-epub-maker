# V2 Migration and Design Decisions

Status: Proposed baseline for V2 implementation

This document records the decisions made after completing the V1 rebuild and reviewing the legacy implementation. V2 should extend the V1 architecture rather than reintroduce the legacy architecture.

## 1. V1 baseline

V1 is intentionally a minimal rewrite. Its purpose is to provide a stable pipeline that preserves source text as much as practical while producing a valid EPUB.

The core phases are:

1. Model: `Book`, `Volume`, `Chapter`, `Paragraph`, with stable serialization.
2. Normalize: encoding, BOM, newline normalization, and leading full-width-space handling. Normalization does not intentionally change the meaning of the source text.
3. Parser: TXT → Book, producing volume, chapter, paragraph, and warnings.
4. Intermediate: Book → `book.json`; Chapter → `chapters/*.json`. The design must remain practical for books containing thousands of chapters.
5. EPUB: Intermediate → Markdown → Pandoc → EPUB, with cover, metadata, TOC, volume/chapter hierarchy, and CSS handled through the renderer pipeline.
6. Validation: parser validation, EPUB structure checks, and EPUBCheck integration.

V1 should remain the stable foundation. V2 should add extension points around this pipeline rather than replace its model, intermediate representation, parser contract, or Pandoc-first renderer.

## 2. Legacy migration policy

The legacy implementation contains several transformations and conveniences that are not appropriate to migrate wholesale. V2 keeps only transformations whose behavior can be made explicit and predictable.

| Legacy feature | V2 decision | Notes |
|---|---|---|
| OpenCC Simplified → Traditional | Keep | Enabled by default; conversion profile remains configurable/extensible. |
| Junk cleaner | Keep | User-configured, remove-only, with explicit target and matcher semantics. |
| Quote conversion | Keep | Independent text transformation. |
| Arabic numeral conversion | Do not migrate | High risk of changing dates, IDs, URLs, formulas, versions, and other legitimate text. |
| Chapter renumbering | Do not migrate | Can change source semantics and invalidate chapter references. |

V2 is not intended to be a complete behavioral clone of `cn-epub-maker`. Compatibility is subordinate to predictable behavior and the V1 architecture.

## 3. Transformation pipeline

The default V2 text pipeline is:

```text
TXT
 ↓
Normalize
 ↓
Junk Cleaner
 ↓
OpenCC
 ↓
Quote Conversion
 ↓
Parser
 ↓
Book
 ↓
Intermediate
 ↓
EPUB
 ↓
Validation
```

The ordering is intentional.

- Normalize operates on the source representation and produces stable input for later stages.
- Junk Cleaner operates on normalized source text, so user rules are written against the source representation rather than against converted text.
- OpenCC performs the language transformation after source cleanup.
- Quote conversion is a presentation-oriented text transformation after language conversion.
- Parser is responsible for document structure and must not silently perform these transformations.

Transforms should be independently testable and should expose enough information to produce statistics and warnings consistently.

## 4. Full Source Mode

V2 retains an officially supported full-source mode. In this mode, content transformations are disabled, but Normalize still runs.

```text
TXT
 ↓
Normalize
 ↓
Parser
```

This mode means that source content is not intentionally transformed. It does not promise byte-for-byte preservation of the input file: encoding representation, BOM, newline representation, and other normalization concerns may still be changed as defined by Phase 2.

The distinction is important:

- Normalize makes the source representation stable and usable.
- Transform changes the content according to an explicit user request or configured output policy.

## 5. OpenCC

OpenCC is retained because the primary use case is converting Simplified Chinese sources into Traditional Chinese output.

The default V2 behavior is OpenCC enabled. Users must be able to disable it, including when using Full Source Mode.

The implementation should retain a conversion-profile abstraction rather than hard-code the public API around one profile. V2 may initially expose the Simplified → Traditional profile used by the project, while leaving room for additional OpenCC profiles later.

OpenCC failures follow the general transform failure policy described below: a safely recoverable transformation problem should produce a warning and allow generation to continue; a failure that makes the resulting output untrustworthy should be treated as an error and stop output generation.

## 6. Junk Cleaner

Junk Cleaner is a parser-preprocessing transformation. It does not decide automatically what is junk. It removes only content explicitly selected by user-defined rules.

### 6.1 Configuration ownership

Junk rules are stored separately from the general book configuration. This keeps potentially numerous and reusable cleanup rules maintainable and makes it possible to reuse the same rules across books.

A conceptual configuration is:

```yaml
junk_cleaner:
  enabled: true
  rules:
    - target: line
      match:
        type: exact
        value: "本章完"

    - target: block
      match:
        type: contains
        value: "本站提供"

    - target: line
      match:
        type: regex
        value: "^广告：.*$"
```

The exact external configuration format may evolve, but the semantic contract below should remain stable.

### 6.2 Targets

V2 provides two cleanup targets:

- `line`: one normalized source line is the target. Matching cannot cross a newline boundary.
- `block`: a continuous text block separated by blank lines is the target. A block may contain multiple lines, but matching cannot cross a blank-line block boundary.

The term `target` is preferred over the previously discussed generic term `scope`, because it describes the unit that may actually be removed.

Cleaner does not use Parser `Paragraph` or `Chapter` objects because it runs before parsing. EPUB `<p>` and `<br>` are renderer output concepts and must not define cleaner semantics.

### 6.3 Matchers

Each rule has one matcher:

- `exact`: the complete target must equal the configured value.
- `contains`: the target contains the configured value.
- `regex`: the configured regular expression matches within the target.

All three matchers have the same action semantics: if the target matches, the **entire target is removed**. `contains` and `regex` do not perform substring replacement.

This gives the cleaner one predictable model:

```text
split into targets
 ↓
match target
 ↓
remove target
```

### 6.4 Rule ordering

Rules execute in user-specified order. Each rule receives the output produced by the preceding rule. Targetization is therefore performed again for each rule, making the behavior explicit and deterministic.

### 6.5 Structural boundaries

A rule must never match across its target boundary.

- A line rule cannot cross a newline.
- A block rule cannot cross a blank-line boundary.
- Cleaner does not cross or infer chapter boundaries because chapters do not exist yet.

Cleaner does not perform chapter or paragraph restructuring.

### 6.6 Empty content

Cleaner does not decide whether an empty paragraph, empty block, or other structural artifact should be removed as a document-structure decision. Such decisions belong to the parser and validation policies.

Cleaner must not silently introduce a second normalization pass.

### 6.7 Statistics and warnings

Every rule should contribute execution statistics. At minimum, the report should expose the number of matched/removed targets for each rule.

For example:

```text
Junk Cleaner:
  rule 1: removed 12 lines
  rule 2: removed 3 blocks
  rule 3: removed 0 lines
```

Zero matches are normal and are **not warnings**.

Invalid configuration or an invalid regular expression is a warning. The invalid rule is skipped and later valid rules continue to run.

Cleaner statistics do not determine build success or failure.

### 6.8 Remove-only boundary

V2 Junk Cleaner is intentionally remove-only. Arbitrary replacement is not part of this contract. If a future requirement needs replacement, it should be introduced as a separate transformation with its own semantics rather than turning Junk Cleaner into a general-purpose text rewriting engine.

## 7. Quote conversion

Quote conversion is retained as an independent transformation because its behavior is limited and predictable. The intended conversion is from common curly quote forms to Chinese quotation forms such as `「」` and `『』`, according to the project's defined mapping.

Already-correct Chinese quotation marks must remain unchanged, and the transformation must be idempotent: applying it twice must not continue changing the text.

Quote conversion runs after OpenCC and after Junk Cleaner.

## 8. Transform failure policy

V2 uses two classes of transformation failure:

1. Recoverable transformation problems: emit a warning, skip the affected transformation/rule, and continue producing the EPUB.
2. Unrecoverable problems that make the output untrustworthy: emit an error and stop output generation.

This follows the V1 validation philosophy: problems that do not prevent a trustworthy EPUB should be visible as warnings rather than unnecessarily blocking generation.

A zero-match rule is not a failure.

## 9. Transformation metadata

Transformation metadata is retained in Intermediate artifacts for reproducibility and debugging. It is not written into EPUB metadata.

Conceptually, `book.json` may record information such as:

```json
{
  "transformations": {
    "opencc": {
      "enabled": true,
      "profile": "s2t"
    },
    "junk_cleaner": {
      "enabled": true,
      "rules": "junk-rules.yaml"
    },
    "quote_conversion": {
      "enabled": true
    }
  }
}
```

The exact schema should follow the existing Intermediate serialization contract when implemented.

The purpose is auditability and reproducible builds, not reader-facing EPUB metadata.

## 10. Parser configuration

Legacy parsing customization, such as volume and chapter patterns, is worth retaining where it provides useful input flexibility. It belongs to Parser configuration and must remain separate from text transformations.

Parser configuration determines document structure:

```text
Volume
Chapter
Paragraph
```

It must not silently perform OpenCC conversion, junk removal, quote conversion, numeral conversion, or chapter renumbering.

## 11. Renderer profiles

V2 should leave room for renderer/presentation profiles instead of accumulating output-specific conditionals. Future options such as horizontal/vertical writing mode or other EPUB presentation policies should be represented as renderer configuration/profile data where appropriate.

The V1 EPUB backend remains Pandoc-first. Package assembly should remain limited to responsibilities Pandoc cannot safely or conveniently own, such as project-specific packaging adjustments and validation-oriented checks.

## 12. CLI and library boundaries

The configuration model should be the primary representation of build behavior. CLI arguments are one frontend for creating or overriding that configuration, rather than the architecture itself.

This prevents V2 from becoming an unmaintainable collection of independent flags as more optional transformations and renderer profiles are introduced.

## 13. Reproducibility

A build should make it possible to determine which transformations and relevant profiles were applied. Intermediate metadata is the canonical audit record.

Where practical, transformations should be deterministic and idempotent where their semantics permit it. Statistics should make the effects of destructive transforms observable without treating them as validation failures.

## 14. Explicit non-goals

The following legacy behaviors are intentionally outside the V2 migration baseline:

- Global Arabic numeral conversion.
- Automatic chapter renumbering.
- Heuristic junk detection copied from the legacy implementation.
- Arbitrary text replacement through Junk Cleaner.
- Byte-for-byte preservation of the original source file.
- Rebuilding the V1 model, intermediate format, or Pandoc-first renderer merely for compatibility with legacy behavior.

These may be reconsidered only when a concrete use case justifies them and their semantics can be specified safely.

## 15. Current V2 direction

The V2 architecture should therefore be understood as a stable V1 core with explicit extension points:

```text
                    ┌─ Junk Cleaner
                    ├─ OpenCC
Normalize ──────────┼─ Quote Conversion ── Parser
                    └─ future transforms

Parser → Intermediate → Pandoc EPUB → Validation
```

The design goal is not maximum feature parity with the legacy program. It is predictable text processing, explicit user control over destructive changes, reproducible intermediate artifacts, and a renderer architecture that can grow without coupling content transformations to parsing or EPUB packaging.

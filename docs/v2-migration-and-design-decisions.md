# V2 Design

## Status

V2 is a proposed design with implementation still incomplete. The decisions in this document are the current architectural baseline for V2; they are not a claim that the full design has already been implemented.

V2 extends the completed V1 architecture. It should not replace the V1 model, Intermediate boundary, parser contract, or Pandoc-first renderer merely to reproduce legacy behavior.

## Relationship to V1

V1 is the stable core:

```text
Normalize → Parser → Intermediate → Pandoc EPUB → Validation
```

V2 adds explicit extension points around that pipeline. Compatibility with the legacy implementation is subordinate to predictable behavior, explicit configuration, and preservation of the V1 architecture.

## Migration Decisions

| Legacy feature | V2 decision | Boundary |
|---|---|---|
| OpenCC Simplified → Traditional | Keep | Enabled by default; profile remains configurable/extensible. |
| Junk Cleaner | Keep | User-configured, remove-only, explicit target and matcher semantics. |
| Quote Conversion | Keep | Independent transformation with explicit, idempotent behavior. |
| Arabic numeral conversion | Do not migrate | Avoid changing dates, IDs, URLs, formulas, versions, and other legitimate numbers. |
| Chapter renumbering | Do not migrate | Preserve source numbering and references. |

V2 is not a complete behavioral clone of the legacy program.

## Architecture

### Transform Pipeline

The default V2 pipeline is:

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

The order is intentional. Normalize stabilizes the source representation; Junk Cleaner matches the normalized source; OpenCC performs language conversion; Quote Conversion performs presentation-oriented text conversion; Parser then determines document structure.

Transformations must remain separate from Parser. Parser determines structure and must not silently perform content transformations.

### Transform Contract

V2 transformations should expose a common conceptual contract:

```text
input text
   ↓
transformation
   ↓
output text + statistics + warnings
```

Each transformation should be independently testable. Statistics make destructive effects observable without turning normal zero-match behavior into an error.

### Failure and Auditability

V2 uses two classes of transformation failure:

1. Recoverable problems produce a warning, skip the affected transformation or rule, and allow generation to continue.
2. Unrecoverable problems that make the output untrustworthy produce an error and stop output generation.

A zero-match rule is normal and is not a failure.

Transformation metadata belongs in Intermediate artifacts, not EPUB metadata. It provides the canonical audit record for reproducibility and debugging.

Where practical, transformations should be deterministic and idempotent when their semantics permit it.

## Transforms

### OpenCC

OpenCC is retained because converting Simplified Chinese sources to Traditional Chinese output is a primary use case.

V2 enables OpenCC by default, while allowing users to disable it, including through Full Source Mode. The implementation should use a conversion-profile abstraction rather than hard-coding the public interface to one profile.

OpenCC follows the common transform failure policy: safely recoverable problems warn and continue; output that cannot be trusted stops the build.

### Junk Cleaner

Junk Cleaner is a parser-preprocessing transformation. It does not automatically decide what is junk. It removes only content explicitly selected by user-defined rules.

Rules are kept separately from general book configuration so cleanup rules can be maintained and reused independently.

The semantic contract is:

- `target: line` — one normalized source line; matching cannot cross a newline.
- `target: block` — a continuous text block separated by blank lines; matching cannot cross a blank-line boundary.
- `match: exact` — the entire target must equal the configured value.
- `match: contains` — the target contains the configured value.
- `match: regex` — the regular expression matches within the target.

A successful match removes the entire target. `contains` and `regex` do not replace substrings.

Rules execute in user-specified order. Each rule receives the previous rule's output, so targetization is performed again for each rule.

Cleaner runs before Parser and therefore does not know about `Chapter`, `Paragraph`, or EPUB elements. It must not cross line/block boundaries, infer chapter boundaries, restructure the document, or introduce a second normalization pass.

Every rule should report execution statistics, including matched/removed target counts. Zero matches are normal. Invalid configuration or an invalid regular expression produces a warning; the invalid rule is skipped and later valid rules continue.

Junk Cleaner is remove-only. Arbitrary replacement is outside this contract and would require a separate transformation if needed later.

### Quote Conversion

Quote Conversion remains an independent transformation. It converts the project's defined common curly-quote forms to Chinese quotation forms such as `「」` and `『』` while leaving already-correct Chinese quotation marks unchanged.

The mapping must be explicit and idempotent. Quote Conversion runs after Junk Cleaner and OpenCC.

## Modes

### Full Source Mode

V2 retains a complete source mode in which content transformations are disabled:

```text
TXT
 ↓
Normalize
 ↓
Parser
```

Full Source Mode does not promise byte-for-byte preservation. Normalize may still change encoding interpretation, BOM, newline representation, and the defined leading full-width-space representation.

The distinction is:

- Normalize stabilizes the source representation.
- Transformations intentionally change content according to explicit configuration.

## Parser and Renderer Extensions

### Parser Configuration

Useful structural customization from the legacy implementation, such as configurable volume and chapter patterns, may be retained where it provides clear input flexibility.

Parser configuration defines document structure:

```text
Volume
Chapter
Paragraph
```

It must remain separate from content transformations and must not silently perform OpenCC conversion, junk removal, quote conversion, global numeral conversion, or chapter renumbering.

### Renderer Profiles

V2 should support renderer/presentation profiles instead of accumulating output-specific conditionals. Options such as horizontal/vertical writing mode and other EPUB presentation policies should be represented as renderer configuration where appropriate.

The V1 Pandoc-first backend remains the foundation. Project-specific package assembly should remain limited to responsibilities Pandoc cannot safely or conveniently own.

## Configuration and CLI

The configuration model should be the primary representation of build behavior. CLI arguments are a frontend for creating or overriding that configuration, not the architecture itself.

This keeps V2 from becoming an unmaintainable collection of unrelated flags as transformations and renderer profiles grow.

Transformation metadata should record which relevant transformations and profiles were applied. The exact Intermediate schema should follow the existing serialization contract when implemented.

## Non-goals

The V2 migration baseline intentionally excludes:

- global Arabic numeral conversion;
- automatic chapter renumbering;
- heuristic junk detection copied from the legacy implementation;
- arbitrary replacement through Junk Cleaner;
- byte-for-byte preservation of the original source file;
- rebuilding the V1 model, Intermediate format, or Pandoc-first renderer solely for legacy compatibility.

A future exception requires a concrete use case and a new explicit behavioral contract.

## Implementation Order

V2 should be implemented incrementally rather than as one large migration. The architectural order is:

1. establish the common transformation boundary and failure/reporting behavior;
2. add OpenCC with an explicit conversion profile;
3. add Junk Cleaner with its configuration and remove-only semantics;
4. add Quote Conversion as an independent transformation;
5. add useful Parser configuration without coupling it to transformations;
6. add renderer profiles for presentation options;
7. make configuration the stable library/CLI boundary;
8. add Intermediate transformation metadata for reproducibility.

Each extension should keep the V1 core stable and should be covered by focused tests before broader integration testing.

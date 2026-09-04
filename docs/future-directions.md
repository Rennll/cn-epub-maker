# Future Directions

## Writing Mode / Vertical Typesetting

Vertical writing is intentionally deferred. Do not implement it as part of the current typography/layout work unless a concrete requirement or observed reader problem makes it necessary.

### Architectural direction

- Keep writing direction as a renderer/output concern, not part of the core `Book`, `Chapter`, or `Paragraph` content model.
- Reserve a future render configuration concept such as:
  - `writing_mode = "horizontal-tb" | "vertical-rl"`
- The current/default mode remains `horizontal-tb`.
- Do not add an enum, dataclass field, CLI option, or configuration surface yet solely for this future capability.
- Prefer renderer-level or typography-level processing when vertical writing is eventually implemented.
- Keep the Intermediate representation layout-agnostic unless a concrete semantic requirement demonstrates that an inline/layout representation is necessary.

### Expected future concerns

When vertical writing is implemented, treat it as a typography/layout policy rather than simply adding `writing-mode: vertical-rl`. At minimum, evaluate:

- EPUB page progression and right-to-left progression for vertical books;
- CJK punctuation and glyph orientation;
- Latin text orientation;
- numeric runs and best-effort tate-chu-yoko / horizontal-in-vertical treatment;
- URL, email, and code handling;
- basic CJK line-breaking and prohibition rules;
- headings and navigation consistency;
- image orientation;
- explicit CJK font selection and fallback behavior;
- reader-specific compatibility and capability differences, especially Apple Books and Kindle/KDP;
- representative real-device validation before treating presentation behavior as stable.

### Content preservation

- Preserve source text when changing presentation mode.
- Do not convert Arabic numerals to Chinese numerals merely to make vertical presentation look better.
- Keep content normalization (OpenCC, punctuation normalization, junk cleanup) separate from vertical typography/orientation decisions.

### Historical note

The previous architecture implemented vertical writing through CSS plus post-generated EPUB ZIP/XML patching and reader-specific fixes. Future work should not reproduce that pattern. The current renderer already owns XHTML, CSS, OPF, navigation, and EPUB packaging, so vertical writing should be integrated at that boundary rather than by generating an EPUB and patching it afterward.

### Relationship to V2.1 typography/layout

The existing V2.1 typography/layout contracts remain horizontal-writing focused for now. Their semantic paragraph boundaries, Intermediate compatibility, and renderer responsibilities should not be changed merely to reserve vertical writing.

Vertical writing should be treated as a future output/presentation capability built on top of those stable semantic contracts.

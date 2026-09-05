# HanWangKaiMediumChuIn Provenance and License Audit

## Scope

This audit records the provenance, license, repository history, and removal rationale for `fonts/HanWangKaiMediumChuIn.ttf`.

The audit is a project-maintenance record, not legal advice.

## Asset at the audit baseline

At commit `77bc1939691346f3d707dbc30443c79ae47ce7e9` (`main` on 2026-09-05), the repository contained:

- Path: `fonts/HanWangKaiMediumChuIn.ttf`
- Git blob SHA: `15af8a37ee5e77c7197bd18c35a2faf385bceff5`
- Size: approximately 13.7 MB

The asset was not referenced by the current V2/V2.1 renderer or by the current Zhuyin IVS processing path.

## Upstream identity and provenance

`HanWangKaiMediumChuIn` is the font family/name associated with the Wang Free Fonts file:

- Original filename: `wp010-08.ttf`
- Chinese name: 王漢宗中楷體注音 / 中楷注音體
- Font/PostScript family identifier commonly documented as `hwkmci`
- Original creator: Dr. Hann-Tzong Wang (王漢宗)

The archived `wangfonts` repository contains `TrueType/wp010-08.ttf` and identifies it as `HanWangKaiMediumChuIn` / `hwkmci`.

The upstream Wang Fonts project describes the fonts as free Chinese TrueType fonts donated by Prof. Hann-Tzong Wang. Its README states that the 2000 and 2004 donated font collections were distributed under GNU GPL v2.

The repository's current binary was not treated as an unmodified upstream copy: its Git history records project-specific glyph modifications described below.

## License

The upstream project identifies the Wang Free Fonts collection as GNU GPL v2. Some downstream font metadata describes the license as GPL version 2 or any later version. This audit therefore records the upstream license conservatively as **GNU GPL v2**, rather than asserting a broader SPDX expression for the modified repository asset.

If this asset were ever redistributed again, the upstream copyright/license notice and the GPL terms should be preserved and the repository-specific modifications should be documented.

## Repository history

The asset entered this repository in commit `946c478ddd2a837f68a3fa68686b8f9b265421fe` (`Add zhuyin font and fix Kindle vertical bracket display`, 2026-03-08).

That commit describes the font as `HanWangKaiMediumChuIn (王漢宗中楷體注音)` and says that vertical bracket glyphs `﹁﹂﹃﹄` were removed to prevent unwanted Zhuyin annotations on punctuation. The same commit adjusted the legacy CSS font stack for Kindle vertical text.

The asset was subsequently modified in commit `8228c3d40e15613fd32cbb6d2f762b623bdc85d0` (`Replace punctuation glyphs in zhuyin font with Songti TC for vertical text`, 2026-03-08). That commit describes replacing selected punctuation glyphs with Songti TC glyphs for vertical layout and removing the same bracket glyphs from the cmap workaround.

Therefore, the file present at the audit baseline should be considered a **repository-modified derivative of the upstream Wang font**, not merely a pristine upstream distribution copy.

## Relationship to the current Zhuyin implementation

The current Zhuyin IVS path uses:

- `fonts/ToneOZ-Zhuyin-Kai-Traditional.ttf`
- `fonts/phonic_table_Z.txt`
- the current Zhuyin IVS processing code

`HanWangKaiMediumChuIn.ttf` is not the current Zhuyin font dependency. Its historical purpose was tied to the older vertical-layout / Kindle punctuation workaround.

## Removal rationale

The asset is being removed because it is a legacy vertical-layout workaround with no current V2/V2.1 runtime dependency. Removing it avoids retaining an approximately 13.7 MB third-party GPL-derived binary solely for historical behavior that is no longer part of the current renderer.

This removal does **not** change the current Zhuyin IVS assets or implementation.

It also does not establish any claim that the upstream Wang font was improperly licensed. The reason for removal is dependency and maintenance hygiene, not a finding of infringement.

## Future third-party font checklist

If a third-party font is introduced in the future, record at minimum:

1. Upstream project and canonical source.
2. Exact upstream filename and version/release.
3. Copyright holder/author.
4. Exact license text or authoritative license reference.
5. Whether the checked-in binary is original or modified.
6. Any modifications and the commit(s) that made them.
7. Whether the font is actually required by the current renderer/runtime.
8. Required attribution or redistribution notices.

For vertical typography specifically, do not reintroduce this font merely to reproduce the historical Kindle workaround. A future font dependency should be evaluated independently against current reader requirements and licensing terms.

## References

- Wang Fonts upstream mirror: `https://github.com/cghio/wangfonts`
- Archived Wang Fonts snapshot containing `TrueType/wp010-08.ttf`: `https://github.com/dictcp-snapshot/wangfonts`
- Repository commit `946c478ddd2a837f68a3fa68686b8f9b265421fe`: added the font and documented the Kindle vertical bracket workaround.
- Repository commit `8228c3d40e15613fd32cbb6d2f762b623bdc85d0`: modified punctuation glyphs for vertical text.

## Audit conclusion

The asset's upstream identity and GPL provenance are sufficiently traceable for project-history purposes. The checked-in file is a modified derivative used for a historical vertical/Kindle workaround. It is not required by the current architecture, so removal is the preferred maintenance outcome.

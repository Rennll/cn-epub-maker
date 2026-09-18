from __future__ import annotations

import argparse
from pathlib import Path

from novel_epub.models import Book, Chapter, Paragraph, ParagraphBoundary, Volume
from novel_epub.renderers.native import NativeRenderer


def build_acceptance_book(cover: str | None = None) -> Book:
    return Book(
        title="Native Renderer 驗收測試",
        author="cn-epub-maker",
        language="zh-TW",
        cover=cover,
        preamble=[
            Paragraph("這是前言。Traditional Chinese 中文與 punctuation：，。！？：「」『』（）"),
            Paragraph("第二段前言，用來確認前言內容與導覽。"),
        ],
        volumes=[
            Volume(
                sequence=1,
                number="1",
                label="第一卷",
                title="閱讀器驗收",
                chapters=[
                    Chapter(
                        sequence=1,
                        number="1",
                        label="第一章",
                        title="段落與換行",
                        paragraphs=[
                            Paragraph("普通段落。這一段用來觀察首行縮排與行距。"),
                            Paragraph("同一段中的硬換行：第一行\n第二行"),
                            Paragraph("擴展段落，前後應有比普通段落更大的間距。", ParagraphBoundary.EXPANDED),
                            Paragraph("場景切換段落。", ParagraphBoundary.SCENE_BREAK),
                        ],
                    ),
                    Chapter(
                        sequence=2,
                        number="2",
                        label="第二章",
                        title="中英混排與長內容",
                        paragraphs=[
                            Paragraph(
                                "這是一段較長的中文正文，混合 English、1234567890、"
                                "，。！？：「」『』（）以及 email@example.com。"
                            ),
                            Paragraph(
                                "LongUnbrokenToken_"
                                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"
                                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                            ),
                            Paragraph(
                                "長篇內容測試。" * 80
                            ),
                        ],
                    ),
                ],
            ),
            Volume(
                sequence=2,
                number="2",
                label="第二卷",
                title="跨卷導覽",
                chapters=[
                    Chapter(
                        sequence=3,
                        number="3",
                        label="第三章",
                        title="跨卷章節",
                        paragraphs=[
                            Paragraph("這一章確認跨卷後的章節順序與導覽位置。"),
                        ],
                    )
                ],
            ),
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the deterministic EPUB used for native-renderer reader acceptance."
    )
    parser.add_argument("output", type=Path, help="output EPUB path")
    parser.add_argument(
        "--cover",
        type=Path,
        help="optional representative cover image (recommended for RR-16)",
    )
    args = parser.parse_args()

    book = build_acceptance_book(str(args.cover) if args.cover is not None else None)

    NativeRenderer().render(book, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

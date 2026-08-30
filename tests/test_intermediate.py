import json
from pathlib import Path

from novel_epub.intermediate import write_intermediate
from novel_epub.models import Book, Chapter, Paragraph, Volume


def test_intermediate_is_per_chapter_and_preserves_order(tmp_path: Path):
    book = Book(title="書", author="作者")
    book.volumes.append(
        Volume(
            sequence=1,
            number="7",
            label="第七卷",
            title="原始卷名",
            chapters=[
                Chapter(sequence=26, number="26", label="第26章", title="跳號章", paragraphs=[Paragraph("正文 < & >")]),
                Chapter(sequence=27, number="番外", label="番外", title="番外", paragraphs=[Paragraph("第二章")]),
            ],
        )
    )
    root = write_intermediate(book, tmp_path / "intermediate")

    metadata = json.loads((root / "book.json").read_text(encoding="utf-8"))
    assert [c["sequence"] for c in metadata["chapters"]] == [26, 27]
    assert metadata["volumes"][0]["number"] == "7"
    assert metadata["volumes"][0]["chapters"] == [
        {"sequence": 26, "file": "chapters/000001.json"},
        {"sequence": 27, "file": "chapters/000002.json"},
    ]

    first = json.loads((root / "chapters/000001.json").read_text(encoding="utf-8"))
    assert first["number"] == "26"
    assert first["paragraphs"] == [{"text": "正文 < & >"}]
    assert (root / "chapters/000002.json").is_file()

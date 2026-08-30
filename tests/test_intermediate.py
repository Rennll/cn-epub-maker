import json
from pathlib import Path

from novel_epub.intermediate import write_intermediate
from novel_epub.parser import parse_lines


def test_intermediate_is_split_by_chapter(tmp_path: Path):
    result = parse_lines([
        "第一卷 九洲一号群",
        "第1章 A",
        "第一段",
        "",
        "第二段",
        "第二卷 武道筑基",
        "第26章 B",
        "正文",
    ], title="书", author="作者")

    root = write_intermediate(result.book, tmp_path / "intermediate")
    metadata = json.loads((root / "book.json").read_text(encoding="utf-8"))

    assert [entry["sequence"] for entry in metadata["chapters"]] == [1, 2]
    assert metadata["chapters"][0]["number"] == "1"
    assert metadata["chapters"][1]["number"] == "26"

    first = json.loads((root / "chapters/000001.json").read_text(encoding="utf-8"))
    assert [p["text"] for p in first["paragraphs"]] == ["第一段", "第二段"]
    assert sorted(p.name for p in (root / "chapters").glob("*.json")) == [
        "000001.json", "000002.json"
    ]

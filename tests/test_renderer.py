from pathlib import Path

from novel_epub.parser import parse_lines
from novel_epub.renderers.pandoc import _markdown


def test_markdown_keeps_volume_hierarchy_and_chapter_order():
    result = parse_lines([
        "第一卷 九洲一号群",
        "第1章 黄山真君和九洲一号群",
        "正文 & < >",
        "第二卷 武道筑基",
        "第26章 我那与众不同的炼丹炉",
        "第二章正文",
    ], title="修真聊天群", author="圣骑士的传说")

    markdown = _markdown(result.book)
    assert "# 第一卷 九洲一号群" in markdown
    assert "## 第1章 黄山真君和九洲一号群" in markdown
    assert "# 第二卷 武道筑基" in markdown
    assert "## 第26章 我那与众不同的炼丹炉" in markdown
    assert "正文 & < >" in markdown


def test_renderer_module_does_not_change_source_text():
    result = parse_lines(
        ["第1章 A", "引号“原样” 123 & < >"],
        title="书",
        author="作者",
    )
    markdown = _markdown(result.book)
    assert "引号“原样” 123 & < >" in markdown

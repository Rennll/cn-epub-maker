from novel_epub.models import Book, Chapter, Paragraph, Volume
from novel_epub.renderers.pandoc import _markdown


def test_markdown_preserves_volume_and_chapter_hierarchy():
    book = Book(title="測試書", author="作者")
    book.volumes.append(
        Volume(
            sequence=1,
            number="1",
            label="第一卷",
            title="九洲一号群",
            chapters=[
                Chapter(
                    sequence=1,
                    number="1",
                    label="第1章",
                    title="黄山真君和九洲一号群",
                    paragraphs=[Paragraph("　　2019年5月20日，星期一。"), Paragraph("a < b & c > d")],
                )
            ],
        )
    )
    md = _markdown(book)
    assert "# 第一卷 九洲一号群" in md
    assert "## 第1章 黄山真君和九洲一号群" in md
    assert "a < b & c > d" in md
    assert "　　2019年5月20日" in md

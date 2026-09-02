from novel_epub.chinese_numerals import chinese_numeral_to_int


def test_chinese_numeral_conversion():
    cases = {
        "一": 1,
        "十": 10,
        "十一": 11,
        "二十": 20,
        "二十一": 21,
        "一百": 100,
        "一百零一": 101,
        "一百一十": 110,
        "一千零二": 1002,
        "九千九百九十九": 9999,
        "一萬": 10000,
        "一萬零三": 10003,
        "一萬二千三百四十五": 12345,
        "一億": 100000000,
        "兩百": 200,
        "兩百零三": 203,
        "〇": 0,
    }

    for text, expected in cases.items():
        assert chinese_numeral_to_int(text) == expected


def test_chinese_numeral_conversion_rejects_empty_and_unsupported_forms():
    for text in ["", " ", "101", "十百", "一百百", "一億萬"]:
        assert chinese_numeral_to_int(text) is None

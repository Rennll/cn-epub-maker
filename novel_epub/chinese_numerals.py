from __future__ import annotations

_DIGITS = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "兩": 2, "两": 2,
    "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}
_SMALL_UNITS = {"十": 10, "百": 100, "千": 1000}
_LARGE_UNITS = {"万": 10_000, "萬": 10_000, "亿": 100_000_000, "億": 100_000_000}


def chinese_numeral_to_int(text: str) -> int | None:
    """Convert a standard Chinese numeral to an integer.

    Returns None when the input contains unsupported or ambiguous forms.
    Arabic digits are intentionally not handled here.
    """
    s = text.strip()
    if not s or any(ch not in _DIGITS and ch not in _SMALL_UNITS and ch not in _LARGE_UNITS for ch in s):
        return None
    if s.isdigit():
        return None

    total = 0
    section = 0
    number = 0
    for ch in s:
        if ch in _DIGITS:
            number = _DIGITS[ch]
            continue
        if ch in _SMALL_UNITS:
            unit = _SMALL_UNITS[ch]
            if number == 0:
                number = 1
            section += number * unit
            number = 0
            continue
        unit = _LARGE_UNITS[ch]
        section += number
        if section == 0:
            return None
        total += section * unit
        section = 0
        number = 0

    value = total + section + number
    return value if value >= 0 else None

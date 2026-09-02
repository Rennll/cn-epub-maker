from __future__ import annotations

_DIGITS = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "兩": 2, "两": 2,
    "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}
_SMALL_UNITS = {"十": 10, "百": 100, "千": 1000}
_LARGE_UNITS = {"万": 10_000, "萬": 10_000, "亿": 100_000_000, "億": 100_000_000}


def chinese_numeral_to_int(text: str) -> int | None:
    """Convert a conventional Chinese numeral to an integer."""
    s = text.strip()
    if not s or any(ch not in _DIGITS and ch not in _SMALL_UNITS and ch not in _LARGE_UNITS for ch in s):
        return None

    total = 0
    section = 0
    number: int | None = None
    last_small_unit = 10_000
    zero_pending = False

    for ch in s:
        if ch in _DIGITS:
            digit = _DIGITS[ch]
            if digit == 0:
                if number is None:
                    zero_pending = True
                else:
                    number = 0
                continue
            if number is not None and number != 0:
                return None
            number = digit
            continue

        if ch in _SMALL_UNITS:
            unit = _SMALL_UNITS[ch]
            if unit >= last_small_unit:
                return None
            if number is None or number == 0:
                number = 1
            section += number * unit
            number = None
            last_small_unit = unit
            zero_pending = False
            continue

        if number is not None:
            section += number
            number = None
        if section == 0:
            return None
        total += section * _LARGE_UNITS[ch]
        section = 0
        last_small_unit = 10_000
        zero_pending = False

    value = total + section + (number or 0)
    if zero_pending and value == 0:
        return 0
    return value

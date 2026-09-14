from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalLine:
    """A post-transformation physical line; line numbers are 1-based."""

    number: int
    text: str
    blank: bool
    leading_pattern: str | None


@dataclass(frozen=True)
class PhysicalBlock:
    """A contiguous non-blank run, using inclusive 1-based line numbers."""

    index: int
    line_numbers: tuple[int, ...]

    @property
    def line_count(self) -> int:
        return len(self.line_numbers)


@dataclass(frozen=True)
class BlankLineRun:
    """A contiguous blank-line run, using inclusive 1-based line numbers."""

    index: int
    line_numbers: tuple[int, ...]
    preceding_block: int | None
    following_block: int | None

    @property
    def length(self) -> int:
        return len(self.line_numbers)


@dataclass(frozen=True)
class PhysicalDocument:
    lines: tuple[PhysicalLine, ...]
    blocks: tuple[PhysicalBlock, ...]
    blank_runs: tuple[BlankLineRun, ...]


def is_blank_line(text: str) -> bool:
    return not text.strip()


def leading_whitespace_pattern(text: str) -> str:
    if is_blank_line(text):
        raise ValueError("blank lines do not have a leading whitespace pattern")
    prefix = text[: len(text) - len(text.lstrip())]
    if not prefix:
        return "NO_INDENT"
    kinds = []
    for char in prefix:
        kind = (
            "ASCII_SPACE"
            if char == " "
            else "IDEOGRAPHIC_SPACE"
            if char == "\u3000"
            else "TAB"
            if char == "\t"
            else "OTHER"
        )
        if kind not in kinds:
            kinds.append(kind)
    if len(kinds) != 1 or kinds[0] == "OTHER":
        return "MIXED"
    kind = kinds[0]
    count = sum(
        1
        for char in prefix
        if (kind == "ASCII_SPACE" and char == " ")
        or (kind == "IDEOGRAPHIC_SPACE" and char == "\u3000")
        or (kind == "TAB" and char == "\t")
    )
    return f"{kind}_x{count}"


def build_physical_document(lines: list[str] | tuple[str, ...]) -> PhysicalDocument:
    physical = tuple(
        PhysicalLine(
            number=number,
            text=text,
            blank=is_blank_line(text),
            leading_pattern=None if is_blank_line(text) else leading_whitespace_pattern(text),
        )
        for number, text in enumerate(lines, 1)
    )

    blocks: list[PhysicalBlock] = []
    blank_runs: list[BlankLineRun] = []
    block_lines: list[int] = []
    blank_lines: list[int] = []

    def flush_block() -> None:
        if block_lines:
            blocks.append(PhysicalBlock(len(blocks), tuple(block_lines)))
            block_lines.clear()

    def flush_blank() -> None:
        if blank_lines:
            preceding = blocks[-1].index if blocks else None
            following = None
            if blank_lines[-1] < len(physical) and not physical[blank_lines[-1]].blank:
                following = len(blocks)
            blank_runs.append(
                BlankLineRun(
                    index=len(blank_runs),
                    line_numbers=tuple(blank_lines),
                    preceding_block=preceding,
                    following_block=following,
                )
            )
            blank_lines.clear()

    for line in physical:
        if line.blank:
            flush_block()
            blank_lines.append(line.number)
        else:
            flush_blank()
            block_lines.append(line.number)

    flush_block()
    flush_blank()
    return PhysicalDocument(physical, tuple(blocks), tuple(blank_runs))

from dataclasses import dataclass

@dataclass(frozen=True)
class PhysicalLine:
    number: int
    text: str
    blank: bool
    leading_pattern: str | None

@dataclass(frozen=True)
class PhysicalBlock:
    index: int
    line_numbers: tuple[int, ...]

@dataclass(frozen=True)
class BlankLineRun:
    index: int
    line_numbers: tuple[int, ...]
    preceding_block: int | None
    following_block: int | None

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
        kind = "ASCII_SPACE" if char == " " else "IDEOGRAPHIC_SPACE" if char == "\u3000" else "TAB" if char == "\t" else "OTHER"
        if kind not in kinds:
            kinds.append(kind)
    if len(kinds) != 1 or kinds[0] == "OTHER":
        return "MIXED"
    kind = kinds[0]
    return f"{kind}_x{sum(1 for c in prefix if (kind == 'ASCII_SPACE' and c == ' ') or (kind == 'IDEOGRAPHIC_SPACE' and c == '\u3000') or (kind == 'TAB' and c == '\t'))}"

def build_physical_document(lines: list[str] | tuple[str, ...]) -> PhysicalDocument:
    physical = []
    for number, text in enumerate(lines, 1):
        blank = is_blank_line(text)
        physical.append(PhysicalLine(number, text, blank, None if blank else leading_whitespace_pattern(text)))
    blocks = []
    blank_runs = []
    block_lines = []
    blank_lines = []
    def flush_block():
        if block_lines:
            blocks.append(PhysicalBlock(len(blocks), tuple(block_lines)))
            block_lines.clear()
    def flush_blank():
        if blank_lines:
            following = len(blocks) if blank_lines[-1] < len(physical) and not physical[blank_lines[-1]].blank else None
            blank_runs.append(BlankLineRun(len(blank_runs), tuple(blank_lines), blocks[-1].index if blocks else None, following))
            blank_lines.clear()
    for line in physical:
        if line.blank:
            flush_block(); blank_lines.append(line.number)
        else:
            flush_blank(); block_lines.append(line.number)
    flush_block(); flush_blank()
    return PhysicalDocument(tuple(physical), tuple(blocks), tuple(blank_runs))

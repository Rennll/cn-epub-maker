from dataclasses import dataclass

from .physical import PhysicalDocument

@dataclass(frozen=True)
class AnalysisMetadata:
    physical_line_count: int
    nonblank_line_count: int
    blank_line_count: int

@dataclass(frozen=True)
class PhysicalBlockEvidence:
    block_index: int
    line_count: int
    first_format: str
    last_format: str

@dataclass(frozen=True)
class BlankLineRunEvidence:
    length: int
    preceding_block: int | None
    following_block: int | None

@dataclass(frozen=True)
class FormattingPatternStatistics:
    pattern: str
    total_count: int
    block_start_count: int
    block_end_count: int

@dataclass(frozen=True)
class FormattingTransitionStatistics:
    from_pattern: str
    to_pattern: str
    count: int

@dataclass(frozen=True)
class DocumentAnalysis:
    metadata: AnalysisMetadata
    blocks: tuple[PhysicalBlockEvidence, ...]
    blank_line_runs: tuple[BlankLineRunEvidence, ...]
    patterns: tuple[FormattingPatternStatistics, ...]
    transitions: tuple[FormattingTransitionStatistics, ...]


def analyze_document(document: PhysicalDocument) -> DocumentAnalysis:
    nonblank = sum(not line.blank for line in document.lines)
    pattern_total: dict[str, int] = {}
    pattern_start: dict[str, int] = {}
    pattern_end: dict[str, int] = {}
    transitions: dict[tuple[str, str], int] = {}
    block_evidence = []

    by_number = {line.number: line for line in document.lines}
    for block in document.blocks:
        lines = [by_number[number] for number in block.line_numbers]
        first = lines[0].leading_pattern
        last = lines[-1].leading_pattern
        assert first is not None and last is not None
        block_evidence.append(PhysicalBlockEvidence(block.index, block.line_count, first, last))
        pattern_start[first] = pattern_start.get(first, 0) + 1
        pattern_end[last] = pattern_end.get(last, 0) + 1
        for line in lines:
            pattern = line.leading_pattern
            assert pattern is not None
            pattern_total[pattern] = pattern_total.get(pattern, 0) + 1
        for left, right in zip(lines, lines[1:]):
            assert left.leading_pattern is not None and right.leading_pattern is not None
            key = (left.leading_pattern, right.leading_pattern)
            transitions[key] = transitions.get(key, 0) + 1

    blank_evidence = tuple(
        BlankLineRunEvidence(run.length, run.preceding_block, run.following_block)
        for run in document.blank_runs
    )
    patterns = tuple(
        FormattingPatternStatistics(pattern, pattern_total[pattern], pattern_start.get(pattern, 0), pattern_end.get(pattern, 0))
        for pattern in sorted(pattern_total)
    )
    transition_stats = tuple(
        FormattingTransitionStatistics(left, right, transitions[(left, right)])
        for left, right in sorted(transitions)
    )
    return DocumentAnalysis(
        metadata=AnalysisMetadata(len(document.lines), nonblank, len(document.lines) - nonblank),
        blocks=tuple(block_evidence),
        blank_line_runs=blank_evidence,
        patterns=patterns,
        transitions=transition_stats,
    )

from dataclasses import dataclass

from .analysis import (
    BlankLineRunEvidence,
    DocumentAnalysis,
    FormattingPatternStatistics,
    FormattingTransitionStatistics,
    PhysicalBlockEvidence,
)
from .physical import PhysicalDocument


@dataclass(frozen=True)
class DocumentFormattingModel:
    """Formatting evidence derived from one shared PhysicalDocument.

    This model intentionally contains no semantic document structure.
    """

    physical_document: PhysicalDocument
    analysis: DocumentAnalysis

    @property
    def blocks(self) -> tuple[PhysicalBlockEvidence, ...]:
        return self.analysis.blocks

    @property
    def blank_line_runs(self) -> tuple[BlankLineRunEvidence, ...]:
        return self.analysis.blank_line_runs

    @property
    def patterns(self) -> tuple[FormattingPatternStatistics, ...]:
        return self.analysis.patterns

    @property
    def transitions(self) -> tuple[FormattingTransitionStatistics, ...]:
        return self.analysis.transitions


def build_formatting_model(
    document: PhysicalDocument,
    analysis: DocumentAnalysis,
) -> DocumentFormattingModel:
    """Build a formatting model without introducing semantic boundaries."""
    if analysis.metadata.physical_line_count != len(document.lines):
        raise ValueError("analysis must describe the same PhysicalDocument")

    # Analysis is derived from the document, but line counts alone cannot
    # prove object identity. Re-analyze and compare the complete evidence so
    # an analysis from a different document cannot be silently paired with it.
    expected = __import__("novel_epub.analysis", fromlist=["analyze_document"]).analyze_document(document)
    if analysis != expected:
        raise ValueError("analysis must describe the same PhysicalDocument")

    return DocumentFormattingModel(physical_document=document, analysis=analysis)

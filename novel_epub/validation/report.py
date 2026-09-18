from __future__ import annotations

from dataclasses import dataclass, field

from ..parser_stages import WarningItem


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[WarningItem] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

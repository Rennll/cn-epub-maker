from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EpubCheckResult:
    available: bool
    ok: bool
    errors: list[str]


def run_epubcheck(path: str | Path, *, required: bool = False) -> EpubCheckResult:
    """Run the optional external EPUBCheck executable."""
    path = Path(path)
    command = shutil.which("epubcheck")
    if command is None:
        if required:
            return EpubCheckResult(
                available=False,
                ok=False,
                errors=["EPUBCheck executable not found"],
            )
        return EpubCheckResult(available=False, ok=True, errors=[])

    try:
        completed = subprocess.run(
            [command, str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return EpubCheckResult(available=True, ok=False, errors=[str(exc)])

    if completed.returncode == 0:
        return EpubCheckResult(available=True, ok=True, errors=[])

    errors = [output for output in (completed.stdout, completed.stderr) if output]
    if not errors:
        errors.append(f"EPUBCheck exited with status {completed.returncode}")
    return EpubCheckResult(available=True, ok=False, errors=errors)

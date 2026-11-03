"""MRZ validation boundary. A future validator must name its supported format."""

from typing import Protocol

from euroid_forensics.domain.models import StageResult


class MRZValidator(Protocol):
    def validate(self, lines: tuple[str, ...], *, format_name: str) -> StageResult: ...


def stage_status() -> StageResult:
    return StageResult("MRZ validation", "not_run", "No MRZ text or validated parser available.")

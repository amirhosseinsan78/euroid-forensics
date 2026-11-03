"""Local OCR extension contract; no engine is invoked in this phase."""

from dataclasses import dataclass
from typing import Protocol

from euroid_forensics.domain.models import StageResult


@dataclass(frozen=True)
class TextSpan:
    text: str
    box: tuple[int, int, int, int]
    confidence: float | None  # Engine confidence, never authenticity confidence.


@dataclass(frozen=True)
class OCRResult:
    spans: tuple[TextSpan, ...] = ()
    language: str | None = None
    engine_version: str | None = None
    model_version: str | None = None


class OCREngine(Protocol):
    def extract(self, image, *, language: str, timeout_seconds: float) -> OCRResult: ...


def stage_status() -> StageResult:
    return StageResult("OCR", "not_run", "No OCR engine configured; no text was extracted.")

"""Extension contract for future independently evaluated anomaly detectors."""

from typing import Protocol

from euroid_forensics.domain.models import Finding, StageResult


class FraudDetector(Protocol):
    def observe(self, image, *, profile_version: str) -> tuple[Finding, ...]: ...


def stage_status() -> StageResult:
    return StageResult(
        "Fraud detection",
        "not_run",
        "No validated model or detector configured. No fraud assessment performed.",
    )

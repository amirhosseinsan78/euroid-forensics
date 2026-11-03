"""Version-specific document profile registry; intentionally empty."""

from dataclasses import dataclass

from euroid_forensics.domain.models import StageResult


@dataclass(frozen=True)
class DocumentTemplate:
    country: str
    document_version: str
    reference_source: str
    profile_version: str


class TemplateRegistry:
    def __init__(self) -> None:
        self._profiles: dict[tuple[str, str], DocumentTemplate] = {}

    def lookup(self, country: str, version: str) -> DocumentTemplate | None:
        return self._profiles.get((country, version))


def stage_status() -> StageResult:
    return StageResult(
        "Document templates",
        "unsupported",
        "No official country/version profiles installed. Document type is unknown.",
    )

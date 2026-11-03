"""Serializable observations. Confidence never represents document authenticity."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int

    def validate(self, width: int, height: int) -> None:
        if (
            min(self.x, self.y) < 0
            or min(self.width, self.height) < 32
            or self.x + self.width > width
            or self.y + self.height > height
        ):
            raise ValueError("Region must be within the image and at least 32 × 32 pixels.")


@dataclass(frozen=True)
class Finding:
    code: str
    title: str
    detail: str
    severity: str = "info"
    confidence: str = "Uncalibrated heuristic"


@dataclass(frozen=True)
class StageResult:
    stage: str
    status: str
    detail: str


@dataclass(frozen=True)
class SideReport:
    side: str
    filename: str
    sha256: str
    width: int
    height: int
    region: Region | None
    metrics: dict[str, float]
    boundary: tuple[tuple[int, int], ...]
    findings: tuple[Finding, ...]
    stages: tuple[StageResult, ...]
    status: str


LIMITATIONS = (
    "Preliminary image quality review only; authenticity and identity are not assessed.",
    "Thresholds and boundary candidates are uncalibrated heuristics, not probabilities.",
    "OCR, MRZ validation, country/version templates and fraud detection are not run.",
    "RGB images cannot verify UV/IR, tactile features, hologram motion or chip signatures.",
    "No issuing-authority checks are performed. A lack of warnings does not prove authenticity.",
)


@dataclass(frozen=True)
class AnalysisReport:
    id: str
    created_at: str
    sides: tuple[SideReport, ...]
    limitations: tuple[str, ...] = LIMITATIONS
    schema_version: int = 1
    analyzer_version: str = "quality-v0.1.0"

    @classmethod
    def create(cls, sides: tuple[SideReport, ...]) -> "AnalysisReport":
        if not sides:
            raise ValueError("Load at least one card side before analysis.")
        return cls(str(uuid4()), datetime.now(timezone.utc).isoformat(), sides)

    def to_dict(self) -> dict:
        return asdict(self)

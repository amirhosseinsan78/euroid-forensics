"""UI-independent orchestration with cooperative cancellation and stable inputs."""

from dataclasses import replace
from threading import Event

from euroid_forensics.document_validation import mrz, templates
from euroid_forensics.domain.models import AnalysisReport, Region, SideReport
from euroid_forensics.fraud_detection import base as fraud
from euroid_forensics.image_processing.loading import ImageAsset
from euroid_forensics.image_processing.quality import assess_quality
from euroid_forensics.ocr import base as ocr


class AnalysisCancelled(Exception):
    pass


def check_cancelled(cancel: Event) -> None:
    if cancel.is_set():
        raise AnalysisCancelled()


def analyze(
    assets: dict[str, ImageAsset],
    regions: dict[str, Region | None],
    cancel: Event,
) -> AnalysisReport:
    reports = []
    for side, asset in assets.items():
        check_cancelled(cancel)
        region = regions.get(side)
        metrics, boundary, findings = assess_quality(asset, region)
        check_cancelled(cancel)
        reports.append(
            SideReport(
                side,
                asset.filename,
                asset.sha256,
                asset.width,
                asset.height,
                region,
                metrics,
                boundary,
                findings,
                (
                    ocr.stage_status(),
                    mrz.stage_status(),
                    templates.stage_status(),
                    fraud.stage_status(),
                ),
                "insufficient_quality"
                if any(f.severity == "warning" for f in findings)
                else "preliminary_only",
            )
        )
    check_cancelled(cancel)
    report = AnalysisReport.create(tuple(reports))
    if len(reports) < 2:
        report = replace(
            report,
            limitations=report.limitations
            + ("Only one side was supplied; the other side has not been reviewed.",),
        )
    return report

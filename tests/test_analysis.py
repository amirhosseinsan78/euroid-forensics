from dataclasses import replace
from threading import Event

import cv2
import numpy as np
import pytest

from euroid_forensics.document_validation.templates import TemplateRegistry
from euroid_forensics.domain.models import Region
from euroid_forensics.image_processing.quality import assess_quality
from euroid_forensics.services import AnalysisCancelled, analyze
from euroid_forensics.ui.report_view import report_html


def test_blur_lowers_detail_and_preserves_source(assets):
    original = assets["front"]
    before = original.bgr.copy()
    blurred = replace(original, bgr=cv2.GaussianBlur(original.bgr, (41, 41), 12))
    sharp_metrics, _, _ = assess_quality(original)
    blurred_metrics, _, findings = assess_quality(blurred)
    assert sharp_metrics["laplacian_variance"] > blurred_metrics["laplacian_variance"]
    assert any(f.code == "low_detail" for f in findings)
    np.testing.assert_array_equal(original.bgr, before)


@pytest.mark.parametrize("value,code", [(5, "underexposed"), (250, "overexposed")])
def test_exposure_and_contrast_are_reported(assets, value, code):
    image = replace(assets["front"], bgr=np.full((400, 600, 3), value, np.uint8))
    _, boundary, findings = assess_quality(image)
    codes = {f.code for f in findings}
    assert {code, "low_contrast", "low_detail", "clipping", "boundary_missing"} <= codes
    assert not boundary


def test_boundary_is_candidate_and_roi_uses_source_coordinates(assets):
    region = Region(50, 30, 1000, 650)
    _, boundary, findings = assess_quality(assets["front"], region)
    assert len(boundary) == 4
    assert all(100 <= x <= 1000 and 70 <= y <= 650 for x, y in boundary)
    candidate = next(f for f in findings if f.code == "boundary_candidate")
    assert candidate.confidence == "Low — geometry only"


@pytest.mark.parametrize(
    "region", [Region(-1, 0, 100, 100), Region(0, 0, 10, 100), Region(1000, 0, 200, 100)]
)
def test_out_of_bounds_or_tiny_roi_rejected(assets, region):
    with pytest.raises(ValueError, match="Region"):
        assess_quality(assets["front"], region)


def test_report_separates_unavailable_stages_and_missing_side(assets):
    report = analyze({"front": assets["front"]}, {"front": Region(0, 0, 400, 400)}, Event())
    side = report.sides[0]
    assert side.region.width == 400
    assert {s.stage for s in side.stages} == {
        "OCR",
        "MRZ validation",
        "Document templates",
        "Fraud detection",
    }
    assert all(s.status in {"not_run", "unsupported"} for s in side.stages)
    assert any("Only one side" in limit for limit in report.limitations)
    assert TemplateRegistry().lookup("any", "unknown") is None
    html = "".join(report_html(report.to_dict())).lower()
    assert "authenticity and identity are not assessed" in html
    assert "authenticity confirmed" not in html and "genuine" not in html


def test_cancelled_request_has_no_partial_report(assets):
    cancel = Event()
    cancel.set()
    with pytest.raises(AnalysisCancelled):
        analyze(assets, {}, cancel)
    with pytest.raises(ValueError, match="at least one"):
        analyze({}, {}, Event())


def test_saved_view_escapes_untrusted_filenames(assets):
    image = replace(assets["front"], filename="<img src=x onerror=alert(1)>.png")
    report = analyze({"front": image}, {}, Event())
    html = "".join(report_html(report.to_dict()))
    assert "<img" not in html
    assert "&lt;img" in html

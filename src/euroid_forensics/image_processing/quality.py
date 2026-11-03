"""Explainable acquisition-quality heuristics, not forensic classification."""

import cv2
import numpy as np

from euroid_forensics.domain.models import Finding, Region
from euroid_forensics.image_processing.loading import ImageAsset

THRESHOLDS = {
    "laplacian_variance_min": 100.0,
    "mean_luminance_min": 55.0,
    "mean_luminance_max": 210.0,
    "contrast_std_min": 15.0,
    "clipped_fraction_max": 0.35,
    "evaluation_max_edge": 1600.0,
}


def assess_quality(
    asset: ImageAsset,
    region: Region | None = None,
) -> tuple[dict[str, float], tuple[tuple[int, int], ...], tuple[Finding, ...]]:
    image = asset.bgr
    offset_x = offset_y = 0
    if region:
        region.validate(asset.width, asset.height)
        offset_x, offset_y = region.x, region.y
        image = image[region.y : region.y + region.height, region.x : region.x + region.width]
    scale = min(1.0, THRESHOLDS["evaluation_max_edge"] / max(image.shape[:2]))
    if scale < 1:
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness, contrast = float(gray.mean()), float(gray.std())
    dark, bright = float(np.mean(gray <= 10)), float(np.mean(gray >= 245))
    metrics = {
        "laplacian_variance": round(sharpness, 2),
        "mean_luminance": round(brightness, 2),
        "contrast_std": round(contrast, 2),
        "dark_fraction": round(dark, 4),
        "bright_fraction": round(bright, 4),
        "evaluation_scale": round(scale, 6),
        **THRESHOLDS,
    }
    findings = []
    if sharpness < THRESHOLDS["laplacian_variance_min"]:
        findings.append(
            Finding(
                "low_detail",
                "Limited sharpness / detail",
                f"Laplacian variance {sharpness:.1f} < 100. "
                "Blur or a uniform surface may explain this signal.",
                "warning",
            )
        )
    else:
        findings.append(
            Finding(
                "detail_measured",
                "Image detail measured",
                f"Laplacian variance {sharpness:.1f}; noise can inflate this value.",
            )
        )
    if brightness < THRESHOLDS["mean_luminance_min"]:
        findings.append(
            Finding(
                "underexposed",
                "Low overall illumination",
                f"Mean luminance {brightness:.1f}/255 < 55.",
                "warning",
            )
        )
    elif brightness > THRESHOLDS["mean_luminance_max"]:
        findings.append(
            Finding(
                "overexposed",
                "High overall illumination",
                f"Mean luminance {brightness:.1f}/255 > 210.",
                "warning",
            )
        )
    else:
        findings.append(
            Finding(
                "illumination_measured",
                "Overall illumination measured",
                f"Mean luminance {brightness:.1f}/255, within provisional range.",
            )
        )
    if max(dark, bright) > THRESHOLDS["clipped_fraction_max"]:
        findings.append(
            Finding(
                "clipping",
                "Large near-black or near-white area",
                f"Near-black {dark:.0%}; near-white {bright:.0%}. "
                "Background or glare may explain this signal.",
                "warning",
            )
        )
    if contrast < THRESHOLDS["contrast_std_min"]:
        findings.append(
            Finding(
                "low_contrast",
                "Limited contrast",
                f"Luminance standard deviation {contrast:.1f} < 15.",
                "warning",
            )
        )

    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    boundary = ()
    total_area = gray.shape[0] * gray.shape[1]
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:30]:
        if cv2.contourArea(contour) < total_area * 0.12:
            continue
        polygon = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(polygon) != 4 or not cv2.isContourConvex(polygon):
            continue
        _, (w, h), _ = cv2.minAreaRect(polygon)
        if min(w, h) <= 0 or not 1.2 <= max(w, h) / min(w, h) <= 2.2:
            continue
        boundary = tuple(
            (int(round(x / scale)) + offset_x, int(round(y / scale)) + offset_y)
            for x, y in polygon.reshape(-1, 2)
        )
        findings.append(
            Finding(
                "boundary_candidate",
                "Possible card boundary",
                "A large convex quadrilateral was found. It may be another "
                "rectangular object. Green overlay is a candidate only.",
                confidence="Low — geometry only",
            )
        )
        break
    if not boundary:
        findings.append(
            Finding(
                "boundary_missing",
                "No reliable boundary candidate",
                "Try a contrasting background and include all card corners. "
                "No boundary is not evidence of fraud.",
                confidence="Low",
            )
        )
    return metrics, boundary, tuple(findings)

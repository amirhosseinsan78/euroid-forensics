"""Escaped read-only presentation shared by live and saved snapshots."""

from html import escape

from euroid_forensics.domain.report_validation import validate_report


def _html(value: str | int | float) -> str:
    """Escape every interpolated value, including already-validated numbers."""
    return escape(str(value), quote=True)


def report_html(report: object) -> tuple[str, str, str]:
    report = validate_report(report)
    findings, metrics = [], []
    for side in report["sides"]:
        region = side["region"]
        scope = (
            f"Region ({region['x']}, {region['y']}, {region['width']} × {region['height']})"
            if region
            else "Full image"
        )
        title = f"<h2>{escape(side['side'].upper())} · {escape(scope)}</h2>"
        findings.append(title)
        status = (
            "Insufficient quality — review warnings"
            if side["status"] == "insufficient_quality"
            else "Preliminary quality review only"
        )
        findings.append(
            f"<p><b>{status}</b><br>{escape(side['filename'])} · "
            f"{_html(side['width'])} × {_html(side['height'])} px</p>"
        )
        for finding in side["findings"]:
            label = "WARNING" if finding["severity"] == "warning" else "OBSERVATION"
            findings.append(
                f"<h3>{label} · {escape(finding['title'])}</h3>"
                f"<p>{escape(finding['detail'])}<br>"
                f"<small>Confidence: {escape(finding['confidence'])}</small></p>"
            )
        findings.append("<h3>Additional analysis stages</h3>")
        for stage in side["stages"]:
            findings.append(
                f"<p><b>{escape(stage['stage'])} — {escape(stage['status'])}</b>"
                f"<br>{escape(stage['detail'])}</p>"
            )
        metrics.append(title + "<table cellpadding='6'>")
        for key, value in side["metrics"].items():
            metrics.append(
                f"<tr><td>{_html(key.replace('_', ' '))}</td><td>{_html(value)}</td></tr>"
            )
        metrics.append("</table>")
        metrics.append(f"<p>Original-byte SHA-256:<br>{escape(side['sha256'])}</p>")
    limits = "<h2>Scope & limitations</h2>" + "".join(
        f"<p>• {escape(item)}</p>" for item in report["limitations"]
    )
    limits += (
        "<p>ROI coordinates use the EXIF-oriented displayed image. Quality scores depend "
        "on scene content, resolution and selected region. Boundary geometry is not "
        "an official card template match.</p>"
        f"<p>Analysis: {escape(report['analyzer_version'])}<br>"
        f"Created (UTC): {escape(report['created_at'])}</p>"
    )
    return "".join(findings), "".join(metrics), limits

"""Fail closed on untrusted SQLite snapshots before any presentation or coercion."""

import math
import re
from datetime import datetime, timedelta
from uuid import UUID


class InvalidReport(ValueError):
    """A snapshot does not conform to the supported bounded schema."""


def _reject(field):
    # Error text uses our schema paths, never attacker-controlled field values.
    raise InvalidReport(f"Invalid saved report: {field}.")


def _object(value, keys, field):
    if type(value) is not dict or set(value) != set(keys.split()):
        _reject(field)


def _text(value, field, maximum=4096):
    if type(value) is not str or not 1 <= len(value) <= maximum:
        _reject(field)


def _integer(value, field, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        _reject(field)


def _sequence(value, field, minimum, maximum):
    if type(value) not in (list, tuple) or not minimum <= len(value) <= maximum:
        _reject(field)


def _choice(value, choices, field):
    if type(value) is not str or value not in choices:
        _reject(field)


def validate_metadata(report_id, created_at):
    _text(report_id, "id", 64)
    _text(created_at, "created_at", 64)
    try:
        UUID(report_id)
        timestamp = datetime.fromisoformat(created_at)
        if timestamp.utcoffset() != timedelta(0):
            _reject("created_at UTC timestamp")
    except ValueError:
        _reject("id / created_at")


def validate_report(report: object) -> dict:
    """Return the original, fully checked schema-v1 snapshot or raise ValueError.

    Accept only JSON-compatible built-in types (and tuples from dataclass.asdict).
    In particular bool is not a number, numeric strings are not coerced, and no
    arbitrary object's __str__ / mapping methods are invoked by the renderer.
    """
    _object(report, "id created_at sides limitations schema_version analyzer_version", "root")
    _integer(report["schema_version"], "schema_version", 1, 1)
    validate_metadata(report["id"], report["created_at"])
    _text(report["analyzer_version"], "analyzer_version", 128)
    _sequence(report["limitations"], "limitations", 1, 32)
    for limitation in report["limitations"]:
        _text(limitation, "limitation")
    _sequence(report["sides"], "sides", 1, 2)
    seen = set()
    for side in report["sides"]:
        _object(
            side,
            "side filename sha256 width height region metrics boundary findings stages status",
            "side",
        )
        _choice(side["side"], {"front", "back"}, "side name")
        if side["side"] in seen:
            _reject("duplicate side")
        seen.add(side["side"])
        _text(side["filename"], "filename", 512)
        _text(side["sha256"], "sha256", 64)
        if not re.fullmatch(r"[a-f0-9]{64}", side["sha256"]):
            _reject("sha256")
        width, height = side["width"], side["height"]
        _integer(width, "width", 32, 12000)
        _integer(height, "height", 32, 12000)
        if width * height > 24_000_000:
            _reject("pixel budget")
        region = side["region"]
        if region is not None:
            _object(region, "x y width height", "region")
            _integer(region["x"], "region.x", 0, width)
            _integer(region["y"], "region.y", 0, height)
            _integer(region["width"], "region.width", 32, width)
            _integer(region["height"], "region.height", 32, height)
            if region["x"] + region["width"] > width or region["y"] + region["height"] > height:
                _reject("region bounds")
        metrics = side["metrics"]
        if type(metrics) is not dict or not 1 <= len(metrics) <= 64:
            _reject("metrics")
        for key, value in metrics.items():
            _text(key, "metric key", 100)
            # Bound before isfinite so gigantic ints cannot raise OverflowError.
            if type(value) not in (int, float) or not -1e15 <= value <= 1e15:
                _reject("metric value")
            if not math.isfinite(value):
                _reject("non-finite metric")
        _sequence(side["boundary"], "boundary", 0, 4)
        if len(side["boundary"]) not in (0, 4):
            _reject("boundary vertex count")
        for point in side["boundary"]:
            _sequence(point, "boundary point", 2, 2)
            _integer(point[0], "boundary.x", 0, width)
            _integer(point[1], "boundary.y", 0, height)
        _choice(side["status"], {"insufficient_quality", "preliminary_only"}, "quality status")
        _sequence(side["findings"], "findings", 1, 64)
        for finding in side["findings"]:
            _object(finding, "code title detail severity confidence", "finding")
            for field, maximum in (
                ("code", 128),
                ("title", 512),
                ("detail", 4096),
                ("confidence", 256),
            ):
                _text(finding[field], f"finding.{field}", maximum)
            _choice(finding["severity"], {"info", "warning"}, "finding severity")
        _sequence(side["stages"], "stages", 4, 4)
        stage_names = set()
        for stage in side["stages"]:
            _object(stage, "stage status detail", "stage")
            _choice(
                stage["stage"],
                {"OCR", "MRZ validation", "Document templates", "Fraud detection"},
                "stage name",
            )
            _choice(stage["status"], {"not_run", "unsupported"}, "stage status")
            _text(stage["detail"], "stage detail")
            stage_names.add(stage["stage"])
        if len(stage_names) != 4:
            _reject("duplicate stage")
    return report

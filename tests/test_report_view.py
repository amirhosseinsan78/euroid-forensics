import copy
import json
import sqlite3
from html import escape
from html.parser import HTMLParser
from threading import Event

import pytest

from euroid_forensics.domain.report_validation import InvalidReport
from euroid_forensics.services import analyze
from euroid_forensics.storage.repository import MAX_REPORT_BYTES, ReportRepository
from euroid_forensics.ui.report_view import report_html


@pytest.fixture
def snapshot(assets):
    return json.loads(json.dumps(analyze(assets, {}, Event()).to_dict()))


def change(report, path, value):
    for part in path[:-1]:
        report = report[part]
    report[path[-1]] = value


@pytest.mark.parametrize("root", [None, [], "report", 42, True, {}, {"sides": []}])
def test_bad_roots_fail_with_controlled_error(root):
    with pytest.raises(InvalidReport):
        report_html(root)


@pytest.mark.parametrize(
    "path,value",
    [
        (("schema_version",), True),
        (("schema_version",), 2),
        (("id",), "not a uuid"),
        (("created_at",), "2026-11-03"),
        (("analyzer_version",), {}),
        (("limitations",), "not a list"),
        (("limitations",), [None]),
        (("limitations",), []),
        (("sides",), {}),
        (("sides",), []),
        (("sides", 0), None),
        (("sides", 0, "side"), ["front"]),
        (("sides", 0, "filename"), 123),
        (("sides", 0, "sha256"), "bad"),
        (("sides", 0, "width"), "<img src=file:///x>"),
        (("sides", 0, "width"), True),
        (("sides", 0, "width"), 100.0),
        (("sides", 0, "height"), None),
        (("sides", 0, "height"), -1),
        (("sides", 0, "metrics"), []),
        (("sides", 0, "metrics"), {"bad": "<img src=x>"}),
        (("sides", 0, "metrics"), {"bad": True}),
        (("sides", 0, "metrics"), {"bad": [1]}),
        (("sides", 0, "metrics"), {"bad": float("nan")}),
        (("sides", 0, "metrics"), {"bad": float("inf")}),
        (("sides", 0, "metrics"), {"bad": float("-inf")}),
        (("sides", 0, "metrics"), {"bad": 10**400}),
        (("sides", 0, "metrics"), {1: 1}),
        (("sides", 0, "findings"), "not a list"),
        (("sides", 0, "findings", 0, "title"), {}),
        (("sides", 0, "findings", 0, "severity"), "authentic"),
        (("sides", 0, "stages"), [None] * 4),
        (("sides", 0, "stages", 0, "status"), "authenticity confirmed"),
        (("sides", 0, "boundary"), [[0, 0]]),
        (("sides", 0, "boundary"), [["<svg>", 0]] * 4),
        (("sides", 0, "status"), "unknown"),
        (("sides", 0, "region"), False),
        (("sides", 0, "region"), {"x": "<b>", "y": 0, "width": 32, "height": 32}),
        (("sides", 0, "region"), {"x": True, "y": 0, "width": 32, "height": 32}),
        (("sides", 0, "region"), {"x": 0, "y": 0, "width": "32", "height": 32}),
        (("sides", 0, "region"), {"x": 1090, "y": 0, "width": 32, "height": 32}),
    ],
)
def test_malformed_fields_are_rejected_before_rendering(snapshot, path, value):
    change(snapshot, path, value)
    with pytest.raises(InvalidReport):
        report_html(snapshot)


def test_required_fields_and_resource_bounds(snapshot):
    for path, value in [
        (("sides",), snapshot["sides"] * 2),
        (("limitations",), ["x"] * 33),
        (("sides", 0, "filename"), "x" * 513),
        (("sides", 0, "width"), 12001),
        (("sides", 0, "metrics"), {f"k{i}": i for i in range(65)}),
    ]:
        corrupt = copy.deepcopy(snapshot)
        change(corrupt, path, value)
        with pytest.raises(InvalidReport):
            report_html(corrupt)
    for key in snapshot:
        corrupt = copy.deepcopy(snapshot)
        del corrupt[key]
        with pytest.raises(InvalidReport):
            report_html(corrupt)


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)


def test_all_displayed_text_is_escaped_and_numbers_remain_plain(snapshot):
    payload = '<img src="file:///secret.png" onerror="x"> & <a href="https://x">link</a>'
    side = snapshot["sides"][0]
    side["filename"] = payload
    side["region"] = {"x": 1, "y": 2, "width": 300, "height": 400}
    side["metrics"] = {payload: 123.25}
    for key in ("title", "detail", "confidence"):
        side["findings"][0][key] = payload
    side["stages"][0]["detail"] = payload
    snapshot["limitations"] = [payload]
    snapshot["analyzer_version"] = payload[:128]
    html = "".join(report_html(snapshot))
    parser = Tags()
    parser.feed(html)
    assert not {"img", "a", "script", "iframe", "svg"}.intersection(parser.tags)
    assert escape(payload) in html and "123.25" in html
    assert "1100 × 720" in html and "Region (1, 2, 300 × 400)" in html


def test_non_builtin_objects_are_not_coerced(snapshot):
    class Dangerous:
        def __str__(self):
            raise AssertionError("must not stringify unchecked objects")

    snapshot["sides"][0]["width"] = Dangerous()
    with pytest.raises(InvalidReport):
        report_html(snapshot)


@pytest.mark.parametrize(
    "payload",
    [
        "null",
        "[]",
        '"text"',
        '{"sides":',
        '{"id":1,"id":2}',
        "[" * 2000 + "]" * 2000,
        "x" * (MAX_REPORT_BYTES + 1),
    ],
)
def test_corrupt_database_payloads_fail_closed(tmp_path, payload):
    repository = ReportRepository(tmp_path / "reports.sqlite3")
    repository.list_reports()
    with sqlite3.connect(repository.path) as connection:
        connection.execute("INSERT INTO reports VALUES (?, ?, ?)", ("bad", "now", payload))
    with pytest.raises(InvalidReport):
        repository.load("bad")


def test_invalid_history_metadata_is_controlled(tmp_path):
    repository = ReportRepository(tmp_path / "reports.sqlite3")
    repository.list_reports()
    with sqlite3.connect(repository.path) as connection:
        connection.execute("INSERT INTO reports VALUES (?, ?, ?)", ("bad", 123, "{}"))
    with pytest.raises(InvalidReport):
        repository.list_reports()

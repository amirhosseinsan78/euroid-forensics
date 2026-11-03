import sqlite3
from threading import Event

import pytest

from euroid_forensics.services import analyze
from euroid_forensics.storage.repository import ReportRepository


def test_report_roundtrip_reopen_and_idempotent_save(tmp_path, assets):
    path = tmp_path / "nested" / "reports.sqlite3"
    repository = ReportRepository(path)
    report = analyze(assets, {}, Event())
    repository.save(report)
    repository.save(report)
    reopened = ReportRepository(path)
    assert len(reopened.list_reports()) == 1
    saved = reopened.load(report.id)
    assert saved["sides"][0]["sha256"] == assets["front"].sha256
    assert len(saved["sides"]) == 2 and saved["schema_version"] == 1
    assert saved["limitations"]
    assert "bgr" not in str(saved)
    assert "C:\\" not in str(saved)


def test_missing_and_injection_shaped_ids_are_data(tmp_path):
    repository = ReportRepository(tmp_path / "reports.sqlite3")
    for key in ("missing", "'; DROP TABLE reports; --"):
        with pytest.raises(KeyError):
            repository.load(key)
    assert repository.list_reports() == []


def test_newer_schema_is_not_downgraded(tmp_path):
    path = tmp_path / "future.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=2")
    with pytest.raises(ValueError, match="newer"):
        ReportRepository(path).list_reports()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2


def test_invalid_snapshot_does_not_insert_partial_record(tmp_path, assets):
    repository = ReportRepository(tmp_path / "reports.sqlite3")
    report = analyze(assets, {}, Event())
    report.sides[0].metrics["invalid"] = float("nan")
    with pytest.raises(ValueError):
        repository.save(report)
    assert repository.list_reports() == []

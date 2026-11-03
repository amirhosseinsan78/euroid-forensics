"""Versioned local SQLite report snapshots; never stores source image bytes."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from euroid_forensics.domain.models import AnalysisReport
from euroid_forensics.domain.report_validation import (
    InvalidReport,
    validate_metadata,
    validate_report,
)

MAX_REPORT_BYTES = 1024 * 1024


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidReport("Invalid saved report: duplicate JSON key.")
        result[key] = value
    return result


class ReportRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > 1:
                raise ValueError("This database was created by a newer application version.")
            with connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS reports ("
                    "id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)"
                )
                connection.execute("PRAGMA user_version = 1")
            return connection
        except Exception:
            connection.close()
            raise

    def save(self, report: AnalysisReport) -> None:
        payload = json.dumps(validate_report(report.to_dict()), ensure_ascii=False, allow_nan=False)
        if len(payload.encode("utf-8")) > MAX_REPORT_BYTES:
            raise InvalidReport("Saved report exceeds the size limit.")
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO reports (id, created_at, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(id) DO NOTHING",
                (report.id, report.created_at, payload),
            )

    def list_reports(self, limit: int = 100) -> list[tuple[str, str]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT id, created_at FROM reports ORDER BY created_at DESC LIMIT ?",
                (min(max(limit, 1), 1000),),
            ).fetchall()
        for report_id, created_at in rows:
            validate_metadata(report_id, created_at)
        return rows

    def load(self, report_id: str) -> dict:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT CASE WHEN typeof(payload) = 'text' AND length(CAST(payload AS BLOB)) <= ? "
                "THEN payload END FROM reports WHERE id = ?",
                (MAX_REPORT_BYTES, report_id),
            ).fetchone()
        if not row:
            raise KeyError("Saved report not found.")
        if row[0] is None:
            raise InvalidReport("Invalid saved report: oversized or non-text JSON.")
        try:
            report = json.loads(row[0], object_pairs_hook=_json_object)
        except (ValueError, RecursionError) as exc:
            raise InvalidReport("Invalid saved report JSON.") from exc
        return validate_report(report)

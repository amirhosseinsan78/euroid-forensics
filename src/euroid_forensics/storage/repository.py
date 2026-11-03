"""Versioned local SQLite report snapshots; never stores source image bytes."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from euroid_forensics.domain.models import AnalysisReport


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
        payload = json.dumps(report.to_dict(), ensure_ascii=False, allow_nan=False)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO reports (id, created_at, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(id) DO NOTHING",
                (report.id, report.created_at, payload),
            )

    def list_reports(self, limit: int = 100) -> list[tuple[str, str]]:
        with closing(self._connect()) as connection:
            return connection.execute(
                "SELECT id, created_at FROM reports ORDER BY created_at DESC LIMIT ?",
                (min(max(limit, 1), 1000),),
            ).fetchall()

    def load(self, report_id: str) -> dict:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT payload FROM reports WHERE id = ?", (report_id,)
            ).fetchone()
        if not row:
            raise KeyError("Saved report not found.")
        return json.loads(row[0])

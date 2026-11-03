"""Run with python -m euroid_forensics (or the installed GUI command)."""

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from euroid_forensics.ui.main_window import MainWindow


def main() -> int:
    parser = argparse.ArgumentParser(description="Local preliminary image quality review")
    parser.add_argument("--demo", action="store_true", help="Load synthetic non-identity images")
    parser.add_argument("--theme", choices=("light", "dark"), default="dark")
    parser.add_argument("--db", type=Path, help="Override the local SQLite report path")
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("EuroID Forensics")
    app.setOrganizationName("EuroID Forensics")
    app.setStyle("Fusion")
    window = MainWindow(args.db, args.theme)
    window.show()
    if args.demo:
        QTimer.singleShot(0, window.load_demo)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

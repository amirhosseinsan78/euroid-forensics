"""Desktop acquisition and preliminary review workflow."""

import sqlite3
from functools import partial
from pathlib import Path
from threading import Event

from PySide6.QtCore import QStandardPaths, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from euroid_forensics.domain.models import LIMITATIONS
from euroid_forensics.image_processing.loading import load_image
from euroid_forensics.services import AnalysisCancelled, analyze, check_cancelled
from euroid_forensics.storage.repository import ReportRepository
from euroid_forensics.synthetic import demo_assets
from euroid_forensics.ui.image_view import ImageView
from euroid_forensics.ui.report_view import report_html
from euroid_forensics.ui.theme import apply_theme


class Worker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, job, parent=None):
        super().__init__(parent)
        self.cancel_event = Event()
        self.job = job

    def run(self):
        try:
            check_cancelled(self.cancel_event)
            result = self.job(self.cancel_event)
            check_cancelled(self.cancel_event)
            self.succeeded.emit(result)
        except AnalysisCancelled:
            pass
        except (ValueError, OSError) as exc:
            # Avoid exposing local paths from OS errors.
            self.failed.emit(
                str(exc)
                if isinstance(exc, ValueError)
                else "Could not read the image. Check file access and try again."
            )
        except Exception:
            self.failed.emit("Processing failed. Try a different image or a smaller file.")


def load_job(path, cancel):
    check_cancelled(cancel)
    asset = load_image(path)
    check_cancelled(cancel)
    return asset


class MainWindow(QMainWindow):
    def __init__(self, db_path: Path | None = None, theme: str = "dark"):
        super().__init__()
        self.setWindowTitle("EuroID Forensics · Preliminary Review")
        self.resize(1420, 920)
        self.setMinimumSize(1050, 720)
        self.assets = {}
        self.report = None
        self.worker = None
        self._close_pending = False
        self.repository = ReportRepository(
            db_path
            or Path(
                QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.AppLocalDataLocation
                )
            )
            / "reports.sqlite3"
        )
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 12)
        layout.setSpacing(14)
        self.setCentralWidget(central)

        header = QHBoxLayout()
        logo = QLabel("E / ID")
        logo.setObjectName("badge")
        header.addWidget(logo)
        titles = QVBoxLayout()
        eyebrow = QLabel("LOCAL WORKSPACE  /  MVP v0.1")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("EuroID Forensics")
        title.setObjectName("title")
        titles.addWidget(eyebrow)
        titles.addWidget(title)
        header.addLayout(titles)
        header.addStretch()
        header.addWidget(QLabel("Appearance"))
        self.theme = QComboBox()
        self.theme.setAccessibleName("Appearance")
        self.theme.addItems(["Dark", "Light"])
        self.theme.setCurrentText(theme.title())
        self.theme.currentTextChanged.connect(
            lambda value: apply_theme(QApplication.instance(), value == "Dark")
        )
        header.addWidget(self.theme)
        layout.addLayout(header)
        notice = QLabel(
            "PRELIMINARY REVIEW ONLY  ·  Image quality observations do not "
            "verify authenticity or identity. No validated fraud model is active."
        )
        notice.setObjectName("notice")
        notice.setWordWrap(True)
        layout.addWidget(notice)

        actions = QHBoxLayout()
        self.front_button = self.button("Open front…", lambda: self.choose_image("front"), "Ctrl+O")
        self.back_button = self.button(
            "Open back…", lambda: self.choose_image("back"), "Ctrl+Shift+O"
        )
        self.demo_button = self.button("Synthetic demo", self.load_demo)
        self.analyze_button = self.button("Analyze images", self.start_analysis, "Ctrl+Return")
        self.analyze_button.setObjectName("primary")
        self.cancel_button = self.button("Cancel", self.cancel_work, "Esc")
        self.save_button = self.button("Save result", self.save_report, "Ctrl+S")
        self.history_button = self.button("Saved results", self.show_history)
        for button in (self.front_button, self.back_button, self.demo_button):
            actions.addWidget(button)
        actions.addStretch()
        for button in (
            self.analyze_button,
            self.cancel_button,
            self.save_button,
            self.history_button,
        ):
            actions.addWidget(button)
        layout.addLayout(actions)

        splitter = QSplitter()
        viewer_card = QFrame()
        viewer_card.setObjectName("card")
        viewer_layout = QVBoxLayout(viewer_card)
        viewer_layout.setContentsMargins(10, 10, 10, 10)
        toolbar = QHBoxLayout()
        toolbar.addWidget(self.button("−", lambda: self.current_view().zoom(1 / 1.25)))
        toolbar.addWidget(self.button("+", lambda: self.current_view().zoom(1.25)))
        toolbar.addWidget(
            self.button("Fit image", lambda: self.current_view().fit_image(), "Ctrl+0")
        )
        self.region_button = self.button("Select region", self.toggle_selection)
        self.region_button.setCheckable(True)
        self.region_button.setToolTip(
            "Drag a rectangle of at least 32 × 32 pixels; click again to pan"
        )
        toolbar.addWidget(self.region_button)
        self.clear_region_button = self.button(
            "Full image", lambda: self.current_view().set_region(None)
        )
        toolbar.addWidget(self.clear_region_button)
        self.clear_side_button = self.button("Remove side", self.clear_side)
        toolbar.addWidget(self.clear_side_button)
        viewer_layout.addLayout(toolbar)
        self.image_tabs = QTabWidget()
        self.views = {side: ImageView() for side in ("front", "back")}
        for side, view in self.views.items():
            view.region_changed.connect(self.invalidate_report)
            self.image_tabs.addTab(view, side.title() + " · not loaded")
        self.image_tabs.currentChanged.connect(self.update_scope)
        viewer_layout.addWidget(self.image_tabs)
        self.scope_label = QLabel("Drag to pan · Scroll to zoom · Select region to inspect a crop")
        self.scope_label.setObjectName("eyebrow")
        self.scope_label.setWordWrap(True)
        viewer_layout.addWidget(self.scope_label)
        splitter.addWidget(viewer_card)

        result_card = QFrame()
        result_card.setObjectName("card")
        result_layout = QVBoxLayout(result_card)
        result_header = QLabel("REVIEW FINDINGS")
        result_header.setObjectName("eyebrow")
        result_layout.addWidget(result_header)
        self.summary = QLabel("Ready for images")
        self.summary.setWordWrap(True)
        result_layout.addWidget(self.summary)
        self.result_tabs = QTabWidget()
        self.findings, self.measurements, self.limits = (QTextBrowser() for _ in range(3))
        for browser, label in (
            (self.findings, "Findings"),
            (self.measurements, "Measurements"),
            (self.limits, "Limits"),
        ):
            browser.setOpenExternalLinks(False)
            browser.setOpenLinks(False)
            browser.setAccessibleName(label)
            self.result_tabs.addTab(browser, label)
        self.findings.setHtml(
            "<h2>Begin a local review</h2><p>1. Open front and back images.</p>"
            "<p>2. Optionally select a region on either side.</p>"
            "<p>3. Analyze image quality, then explicitly save the result.</p>"
            "<p>Use Synthetic demo for non-identity test images.</p>"
        )
        self.limits.setPlainText("\n\n".join(LIMITATIONS))
        result_layout.addWidget(self.result_tabs)
        splitter.addWidget(result_card)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([800, 520])
        layout.addWidget(splitter, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setMaximumHeight(5)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.statusBar().showMessage(
            "Offline workspace · Nothing is saved until you choose Save result"
        )
        apply_theme(QApplication.instance(), theme == "dark")
        self.update_controls()

    def button(self, text, callback, shortcut=None):
        button = QPushButton(text)
        button.clicked.connect(callback)
        if shortcut:
            button.setShortcut(shortcut)
            button.setToolTip(f"{text} ({shortcut})")
        return button

    def current_side(self):
        return ("front", "back")[self.image_tabs.currentIndex()]

    def current_view(self):
        return self.views[self.current_side()]

    def update_controls(self):
        busy = self.worker is not None
        for button in (self.front_button, self.back_button, self.demo_button):
            button.setEnabled(not busy)
        self.analyze_button.setEnabled(bool(self.assets) and not busy)
        self.cancel_button.setEnabled(busy)
        self.save_button.setEnabled(self.report is not None and not busy)
        for control in (
            self.image_tabs,
            self.region_button,
            self.clear_region_button,
            self.clear_side_button,
        ):
            control.setEnabled(not busy)
        self.progress.setVisible(busy)

    def choose_image(self, side):
        if self.worker:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Open {side} image",
            "",
            "Card images (*.jpg *.jpeg *.png)",
        )
        if path:
            self.start_worker(
                partial(load_job, Path(path)),
                lambda asset: self.accept_asset(side, asset),
                "Loading image…",
            )

    def accept_asset(self, side, asset):
        self.assets[side] = asset
        self.views[side].set_asset(asset)
        index = ("front", "back").index(side)
        self.image_tabs.setTabText(index, f"{side.title()} · {asset.width} × {asset.height}")
        self.image_tabs.setCurrentIndex(index)
        self.invalidate_report()
        self.update_scope()
        self.statusBar().showMessage(f"{side.title()} image loaded · Original file is unchanged")

    def load_demo(self):
        if not self.worker:
            self.start_worker(
                lambda cancel: demo_assets(), self.accept_demo, "Generating synthetic images…"
            )

    def accept_demo(self, assets):
        for side, asset in assets.items():
            self.accept_asset(side, asset)
        self.image_tabs.setCurrentIndex(0)

    def clear_side(self):
        if self.worker:
            return
        side = self.current_side()
        self.assets.pop(side, None)
        self.views[side].show_empty()
        self.image_tabs.setTabText(self.image_tabs.currentIndex(), side.title() + " · not loaded")
        self.invalidate_report()

    def toggle_selection(self):
        for view in self.views.values():
            view.set_selection_mode(self.region_button.isChecked())

    def update_scope(self, *_):
        view = self.current_view()
        region = view.region
        scope = (
            f"ROI: x={region.x}, y={region.y}, {region.width} × {region.height} px"
            if region
            else "Scope: full image"
        )
        self.scope_label.setText(scope + " · Blue: selected region · Green: possible boundary")

    def invalidate_report(self, *_):
        self.report = None
        for view in self.views.values():
            view.set_boundary()
        self.summary.setText("Images or region changed · Analyze to create a current result")
        self.findings.setPlainText("No current analysis. Choose Analyze images.")
        self.measurements.clear()
        self.limits.setPlainText("\n\n".join(LIMITATIONS))
        self.update_scope()
        self.update_controls()

    def start_analysis(self):
        if not self.assets or self.worker:
            return
        assets = dict(self.assets)
        regions = {side: self.views[side].region for side in assets}
        self.invalidate_report()
        self.start_worker(
            partial(analyze, assets, regions),
            self.accept_report,
            "Analyzing image quality locally…",
        )

    def start_worker(self, job, accept, message):
        if self.worker:
            return
        self.worker = Worker(job, self)
        worker = self.worker

        def receive(result):
            if not worker.cancel_event.is_set():
                accept(result)

        worker.succeeded.connect(receive)
        worker.failed.connect(self.processing_error)
        worker.finished.connect(self.worker_finished)
        self.update_controls()
        self.statusBar().showMessage(message)
        worker.start()

    def processing_error(self, message):
        if self.worker and not self.worker.cancel_event.is_set():
            QMessageBox.warning(self, "Image processing error", message)
            self.statusBar().showMessage("Processing failed · Previous inputs are unchanged")

    def worker_finished(self):
        worker = self.worker
        cancelled = worker.cancel_event.is_set()
        self.worker = None
        worker.deleteLater()
        self.update_controls()
        if cancelled:
            self.statusBar().showMessage("Cancelled · No analysis result saved")
        if self._close_pending:
            self.close()

    def cancel_work(self):
        if self.worker:
            self.worker.cancel_event.set()
            self.statusBar().showMessage("Cancelling after the current bounded operation…")

    def accept_report(self, report):
        self.report = report
        for widget, html in zip(
            (self.findings, self.measurements, self.limits), report_html(report.to_dict())
        ):
            widget.setHtml(html)
        for side in report.sides:
            self.views[side.side].set_boundary(side.boundary)
        warnings = sum(f.severity == "warning" for side in report.sides for f in side.findings)
        self.summary.setText(
            f"{len(report.sides)} side(s) reviewed · {warnings} quality warning(s)\n"
            "Confidence: uncalibrated · Authenticity not assessed"
        )
        self.result_tabs.setCurrentIndex(0)
        self.statusBar().showMessage("Preliminary review complete · Result is not saved yet")

    def save_report(self):
        if self.report is None or self.worker:
            return
        try:
            self.repository.save(self.report)
        except (OSError, ValueError, sqlite3.Error):
            QMessageBox.warning(
                self, "Save failed", "Could not save the report. Check local storage."
            )
            return
        self.statusBar().showMessage(f"Saved locally · {self.repository.path}")

    def show_history(self):
        try:
            reports = self.repository.list_reports()
        except (OSError, ValueError, sqlite3.Error):
            QMessageBox.warning(self, "Storage error", "Could not open the local report database.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Saved results · Local snapshots")
        dialog.resize(1000, 700)
        layout = QVBoxLayout(dialog)
        layout.addWidget(
            QLabel(
                "Saved snapshots contain findings and hashes, not source images. "
                "Showing the most recent 100 results."
            )
        )
        split = QSplitter()
        entries, browser = QListWidget(), QTextBrowser()
        browser.setOpenLinks(False)
        for report_id, created in reports:
            entries.addItem(f"{created[:19].replace('T', ' ')} UTC\n{report_id[:8]}")
        if not reports:
            browser.setPlainText("No saved results. Analyze images and choose Save result.")

        def select(index):
            if 0 <= index < len(reports):
                try:
                    saved = self.repository.load(reports[index][0])
                    parts = report_html(saved)
                    browser.setHtml("<h1>Saved snapshot</h1>" + "".join(parts))
                except (OSError, ValueError, KeyError, sqlite3.Error):
                    browser.setPlainText("This saved result could not be read.")

        entries.currentRowChanged.connect(select)
        split.addWidget(entries)
        split.addWidget(browser)
        split.setSizes([260, 700])
        layout.addWidget(split)
        layout.addWidget(self.button("Close", dialog.accept))
        if reports:
            entries.setCurrentRow(0)
        dialog.exec()

    def closeEvent(self, event):
        if self.worker:
            self._close_pending = True
            self.cancel_work()
            event.ignore()
        else:
            event.accept()

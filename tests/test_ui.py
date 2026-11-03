from threading import Event

import cv2
import pytest
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox

from euroid_forensics.domain.models import Region
from euroid_forensics.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot, tmp_path):
    window = MainWindow(tmp_path / "results.sqlite3")
    qtbot.addWidget(window)
    window.show()
    return window


def idle(qtbot, window):
    qtbot.waitUntil(lambda: window.worker is None, timeout=15000)


def test_full_demo_analysis_save_and_history(window, qtbot):
    assert not window.analyze_button.isEnabled()
    assert not window.save_button.isEnabled()
    qtbot.mouseClick(window.demo_button, Qt.MouseButton.LeftButton)
    idle(qtbot, window)
    assert set(window.assets) == {"front", "back"}
    qtbot.mouseClick(window.analyze_button, Qt.MouseButton.LeftButton)
    idle(qtbot, window)
    assert window.report is not None and len(window.report.sides) == 2
    assert "Authenticity not assessed" in window.summary.text()
    assert "Fraud detection" in window.findings.toPlainText()
    assert "not_run" in window.findings.toPlainText()
    qtbot.mouseClick(window.save_button, Qt.MouseButton.LeftButton)
    assert len(window.repository.list_reports()) == 1

    def inspect_history():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QDialog)
        from PySide6.QtWidgets import QTextBrowser

        assert "Saved snapshot" in dialog.findChild(QTextBrowser).toPlainText()
        dialog.accept()

    QTimer.singleShot(50, inspect_history)
    window.show_history()
    window.views["front"].set_region(Region(140, 110, 300, 300))
    assert window.report is None and not window.save_button.isEnabled()
    assert not window.views["back"]._boundary


def test_file_dialog_front_png_and_back_jpeg(window, qtbot, tmp_path, monkeypatch, assets):
    paths = []
    for side, suffix in (("front", ".png"), ("back", ".jpg")):
        path = tmp_path / ("مصنوعی-" + side + suffix)
        ok, data = cv2.imencode(suffix, assets[side].bgr)
        assert ok
        path.write_bytes(data.tobytes())
        paths.append(path)
    for side, path in zip(("front", "back"), paths):
        monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, p=path: (str(p), ""))
        window.choose_image(side)
        idle(qtbot, window)
    assert set(window.assets) == {"front", "back"}
    assert window.assets["back"].filename.endswith(".jpg")
    before = window.assets["front"]
    bad = tmp_path / "broken.png"
    bad.write_bytes(b"invalid image")
    messages = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: messages.append(args[2]))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(bad), ""))
    window.choose_image("front")
    idle(qtbot, window)
    assert messages and window.assets["front"] is before


def test_roi_drag_after_zoom_uses_pixels_and_invalidates_result(window, qtbot, assets):
    window.accept_demo(assets)
    view = window.views["front"]
    view.fit_image()
    view.zoom(1.4)
    window.region_button.setChecked(True)
    window.toggle_selection()
    start = view.mapFromScene(500, 400)
    end = view.mapFromScene(250, 200)
    qtbot.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=start)
    qtbot.mouseMove(view.viewport(), pos=end)
    qtbot.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert view.region is not None
    assert abs(view.region.x - 250) <= 3 and abs(view.region.y - 200) <= 3
    assert abs(view.region.width - 250) <= 4 and abs(view.region.height - 200) <= 4
    window.start_analysis()
    idle(qtbot, window)
    assert window.report.sides[0].region == view.region
    view.set_region(None)
    assert window.report is None
    window.clear_side()
    assert "front" not in window.assets and view.asset is None


def test_themes_and_zoom_controls(window, assets):
    window.accept_demo(assets)
    window.theme.setCurrentText("Light")
    assert QApplication.palette().window().color().lightness() > 200
    window.theme.setCurrentText("Dark")
    assert QApplication.palette().window().color().lightness() < 60
    view = window.current_view()
    before = view.transform().m11()
    view.zoom(1.25)
    assert view.transform().m11() > before
    view.fit_image()
    assert abs(view.transform().m11() - before) < 0.02


def test_cancellation_and_close_do_not_publish_partial_results(window, qtbot):
    started, release = Event(), Event()
    accepted = []

    def bounded_job(cancel):
        started.set()
        release.wait(5)
        return "should not be published"

    window.start_worker(bounded_job, accepted.append, "Testing cancellation")
    qtbot.waitUntil(started.is_set)
    assert not window.front_button.isEnabled()
    window.cancel_work()
    window.close()
    assert window.worker is not None  # Worker ownership survives the close request.
    release.set()
    idle(qtbot, window)
    assert not accepted and not window.isVisible()


def test_small_roi_drag_clears_prior_selection(window, qtbot, assets):
    window.accept_demo(assets)
    view = window.views["front"]
    window.region_button.setChecked(True)
    window.toggle_selection()
    view.set_region(Region(100, 100, 100, 100))
    position = view.mapFromScene(300, 300)
    qtbot.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=position)
    qtbot.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=position + QPoint(2, 2))
    assert view.region is None

"""Two explicit accessible palettes, with no dependency on external assets."""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication, dark: bool) -> None:
    bg, surface, field, text, muted, border = (
        ("#101722", "#192332", "#111b28", "#e7edf5", "#9cafc3", "#334459")
        if dark
        else ("#edf2f6", "#ffffff", "#f6f8fb", "#17283b", "#53667c", "#c7d3e0")
    )
    palette = QPalette()
    for role, color in {
        QPalette.ColorRole.Window: bg,
        QPalette.ColorRole.WindowText: text,
        QPalette.ColorRole.Base: field,
        QPalette.ColorRole.AlternateBase: surface,
        QPalette.ColorRole.Text: text,
        QPalette.ColorRole.Button: surface,
        QPalette.ColorRole.ButtonText: text,
        QPalette.ColorRole.Highlight: "#176c9c",
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: surface,
        QPalette.ColorRole.ToolTipText: text,
        QPalette.ColorRole.Link: "#63b3ff" if dark else "#176c9c",
    }.items():
        palette.setColor(role, QColor(color))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(muted))
    app.setPalette(palette)
    app.setStyleSheet(f"""
        QWidget {{ font-family: 'Segoe UI'; font-size: 10pt; }}
        QMainWindow, QDialog {{ background: {bg}; }}
        QLabel#title {{ font-size: 22pt; font-weight: 700; }}
        QLabel#eyebrow {{ color: {muted}; font-size: 9pt; font-weight: 600; }}
        QLabel#badge {{ color: #ffffff; background: #176c9c; border-radius: 9px;
                         font-size: 18pt; font-weight: 700; padding: 12px; }}
        QLabel#notice {{ color: {text}; background: {surface}; border: 1px solid {border};
                         border-left: 4px solid #dfac4f; border-radius: 5px; padding: 12px; }}
        QFrame#card {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; }}
        QPushButton, QToolButton, QComboBox {{ background: {surface}; color: {text};
            border: 1px solid {border}; border-radius: 5px; padding: 7px 12px; }}
        QPushButton:hover, QToolButton:hover {{ border-color: #4c9ee7; }}
        QPushButton:focus, QToolButton:focus, QComboBox:focus {{ border: 2px solid #4c9ee7; }}
        QPushButton:disabled {{ color: {muted}; background: {field}; }}
        QPushButton#primary {{ background: #176c9c; color: white; font-weight: 600; }}
        QPushButton:checked {{ background: #176c9c; color: white; }}
        QTabWidget::pane {{ border: 1px solid {border}; background: {surface}; }}
        QTabBar::tab {{ padding: 10px 16px; background: {field}; color: {muted}; }}
        QTabBar::tab:selected {{ background: {surface}; color: {text};
                               border-bottom: 3px solid #339ed3; }}
        QTextBrowser, QListWidget {{ border: 0; padding: 10px; background: {surface}; }}
        QGraphicsView {{ border: 0; background: {field}; }}
        QStatusBar {{ color: {muted}; padding: 4px; }}
        QSplitter::handle {{ background: {bg}; width: 10px; }}
    """)

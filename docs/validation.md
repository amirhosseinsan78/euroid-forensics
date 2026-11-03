# Desktop phase validation

Validated locally on 2026-11-03 with Python 3.12.14, Windows 11 build 26300 x64, PySide6 6.12.0, OpenCV 4.14.0.94, NumPy 2.5.4, Pillow 13.0.0 and pytest 9.2.0. Exact runtime/test package constraints are in `requirements/windows-py312.constraints.txt`.

- `python -m pytest -q`: **31 passed**, using Qt offscreen; no real identity data.
- `python -m ruff check src tests`: passed.
- `python -m pip check`: passed.
- Visible Windows GUI: launched using `pythonw -m euroid_forensics --demo`; analyzed both synthetic sides, observed the possible front boundary and blurred-back warning, and visually inspected Light and Dark palettes. Screenshots were captured for review.
- Automated GUI tests exercise front PNG/back JPEG imports via the file picker boundary, Unicode filenames, malformed-image recovery, zoomed/reverse ROI drag, stale-report invalidation, analysis, explicit save, reopening history, cooperative cancellation and close while work runs.

Tests validate engineering behavior, not forensic detection performance. There is no authenticity model, official validation, real-document benchmark, accuracy claim, or selected supported country profile. No standalone executable was built. A clean Windows 10 machine and other Python versions have not been tested locally; the configured Windows CI matrix is a separate check, not a substitute for a clean-machine release test. Do not mark the full MVP milestone complete based on these results.

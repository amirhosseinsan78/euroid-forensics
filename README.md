# EuroID Forensics

Local desktop software for forensic analysis and fraud detection of European identity cards.

**Status: MVP v0.1, first runnable desktop phase.** Local image review and quality heuristics are implemented. OCR, MRZ validation, official document profiles and fraud classification are extension contracts only and are explicitly shown as not run / unsupported.

Target: 64-bit Windows 10 (1809+) / Windows 11, Python 3.12+. Stack: PySide6, OpenCV, Pillow, NumPy and SQLite. The tested environment and remaining platform checks are recorded in [validation](docs/validation.md). PySide6 is capped below 6.13 to retain the Windows 10 target; see [Qt's platform support](https://doc.qt.io/qt-6.12/windows.html).

Repository: [amirhosseinsan78/euroid-forensics](https://github.com/amirhosseinsan78/euroid-forensics) is **Public**; code, issues, PRs and Actions history are publicly readable. Management: [EuroID Forensics project](https://github.com/users/amirhosseinsan78/projects/1), [MVP v0.1 milestone](https://github.com/amirhosseinsan78/euroid-forensics/milestone/1), [six development issues](https://github.com/amirhosseinsan78/euroid-forensics/issues). Project-board access is managed separately from repository visibility.

## Scope

Assist a human examiner in reviewing visible anomalies in lawfully obtained images of European identity cards. Image observations cannot establish document authenticity or identity. Unsupported document versions and poor images must produce an inconclusive result.

MVP v0.1 will support a deliberately selected, documented subset of document versions; universal European coverage is not promised. See [architecture](docs/architecture.md), [limitations](docs/authenticity-limitations.md), [backlog](docs/backlog.md) and [dependency notices](THIRD_PARTY_NOTICES.md).

## Install and run on Windows

Install 64-bit Python 3.12 or newer with pip and the Python launcher. In PowerShell:

```powershell
git clone https://github.com/amirhosseinsan78/euroid-forensics.git
cd euroid-forensics
git switch feat/mvp-desktop-shell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements/windows-py312.constraints.txt -e ".[dev]"
.\.venv\Scripts\python.exe -m euroid_forensics
```

After the PR is merged, the same files are available on `main`. The constraint snapshot records exact runtime/test versions validated on Windows x64 / Python 3.12; other Python versions can install `-e ".[dev]"` without the constraint file, but need their own verification. No PowerShell activation or execution-policy change is required.

Start with synthetic non-identity samples, or choose a light palette:

```powershell
.\.venv\Scripts\python.exe -m euroid_forensics --demo
.\.venv\Scripts\python.exe -m euroid_forensics --demo --theme light
```

The installed GUI entry point is `.\.venv\Scripts\euroid-forensics.exe`. A standalone PyInstaller executable is not delivered in this phase. Tesseract is not needed to run the application. The optional `ocr` extra only installs a future wrapper dependency; it does not activate OCR or install its native engine/models.

## Review workflow

1. Choose **Open front** and **Open back** to import JPG/JPEG or PNG. One-sided reviews are allowed and explicitly marked incomplete. File size is limited to 25 MiB, dimensions to 24 MP and 12000 pixels per side. Animated images are rejected. EXIF orientation is applied to the displayed pixels; original bytes are unchanged and hashed. Transparent PNGs are composited onto white.
2. Use the wheel or +/− to zoom, drag to pan, or **Fit image** (`Ctrl+0`). **Select region** enables rectangle selection on the current side; selections use displayed-image pixel coordinates. **Full image** clears that side's ROI. Regions smaller than 32 × 32 are cleared. Each side keeps an independent ROI.
3. Choose **Analyze images** (`Ctrl+Enter`). Loading and analysis run outside the UI thread. **Cancel** (`Esc`) discards unfinished output after the current bounded operation; it does not interrupt native OpenCV mid-call. Inputs are locked while work runs.
4. Review findings, measurement values and limitations. Blue marks ROI; dashed green marks a possible rectangular boundary, not a confirmed card. Confidence describes uncalibrated observations, never an authenticity probability. Changing an image or ROI invalidates the current report and disables saving until reanalysis.
5. Choose **Save result** (`Ctrl+S`) to persist a snapshot, then **Saved results** to reopen it. Repeated saves of the same analysis do not create duplicates. Images are not stored in SQLite. Review history contains measurements, selected regions, filename, original hash, timestamps, processing version, stage status and limitations.

Results are stored in Qt's per-user `AppLocalDataLocation` under `reports.sqlite3` (shown after saving), outside the checkout. Use `--db C:\path\reports.sqlite3` to override it. The database is not encrypted. Automatic deletion, retention management and export are not implemented. Use synthetic data in this phase.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check src tests tools
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:QT_QPA_PLATFORM
```

The offscreen variable is only for headless tests; remove it before launching a visible GUI. Tests generate geometric, non-identity fixtures at runtime. A Windows CI matrix is configured for Python 3.12 and 3.13. See [validation](docs/validation.md) for executed results and limitations.

Saved SQLite snapshots are untrusted input: schema/type/range/collection limits are checked before rendering; all dynamic text and numbers are HTML-escaped. Invalid snapshots show a controlled error in history instead of being partially rendered. See [memory evaluation](docs/memory-evaluation.md) for reproducible measurements with two retained 24 MP images and the decoding/display optimizations.

## Layout

```text
src/euroid_forensics/
  ui/                   # PySide6 shell, image viewer, report renderer, palettes
  image_processing/     # bounded decoding and OpenCV quality heuristics
  ocr/                  # OCR contracts, no active engine
  document_validation/  # MRZ contract and empty template registry
  fraud_detection/      # detector contract, no active model
  storage/              # versioned SQLite report snapshots
  domain/               # regions, findings and report contracts
  services.py           # cancellable local analysis orchestration
  synthetic.py          # geometric non-identity demo generator
resources/              # non-sensitive application assets
tests/                  # planned unit/integration/system tests
docs/                   # architecture, scope and task definitions
packaging/              # future Windows build configuration
```

Do not commit actual identity-card images, extracted personal data, case databases, OCR outputs or reports. Use synthetic fixtures only.

## Licensing

Public visibility permits reading the repository; no open-source license is granted for the original project at this stage. The owner will choose its license. Third-party components retain their own licenses. The dependency inventory is preliminary and is not a distribution-ready notice bundle.

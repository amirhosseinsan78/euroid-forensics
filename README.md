# EuroID Forensics

Local desktop software for forensic analysis and fraud detection of European identity cards.

**Status: infrastructure scaffold only. No analysis, OCR, UI, database or detection implementation exists yet.**

Target: Windows 10/11, Python 3.12+. Planned stack: PySide6, OpenCV, local Tesseract OCR through pytesseract, SQLite and PyInstaller.

Repository: [amirhosseinsan78/euroid-forensics](https://github.com/amirhosseinsan78/euroid-forensics) (private). Management: [EuroID Forensics project](https://github.com/users/amirhosseinsan78/projects/1) (private), [MVP v0.1 milestone](https://github.com/amirhosseinsan78/euroid-forensics/milestone/1), [six development issues](https://github.com/amirhosseinsan78/euroid-forensics/issues).

## Scope

Assist a human examiner in reviewing visible anomalies in lawfully obtained images of European identity cards. Image observations cannot establish document authenticity or identity. Unsupported document versions and poor images must produce an inconclusive result.

MVP v0.1 will support a deliberately selected, documented subset of document versions; universal European coverage is not promised. See [architecture](docs/architecture.md), [limitations](docs/authenticity-limitations.md), [backlog](docs/backlog.md) and [dependency notices](THIRD_PARTY_NOTICES.md).

## Development setup (future implementation)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,build]"
```

These commands install dependencies and the empty package. There is no launch command or executable yet. Tesseract and its language data are separate native assets; installation, provenance and packaging remain planned tasks. Dependencies are provisional ranges, not a tested lockfile. Resolve and lock them on Windows before implementation validation.

## Layout

```text
src/euroid_forensics/
  ui/                   # planned PySide6 interface
  image_processing/     # planned image quality and preprocessing
  ocr/                  # planned local OCR adapter
  document_validation/  # planned version-aware consistency checks
  fraud_detection/      # planned explainable anomaly observations
  storage/              # planned SQLite persistence
  domain/               # planned shared contracts
resources/              # non-sensitive application assets
tests/                  # planned unit/integration/system tests
docs/                   # architecture, scope and task definitions
packaging/              # future Windows build configuration
```

Do not commit actual identity-card images, extracted personal data, case databases, OCR outputs or reports. Use synthetic fixtures only. All package directories are placeholders.

## Licensing

No open-source license is granted for the original project at this stage; the owner will choose its license. Third-party components retain their own licenses. The dependency inventory is preliminary and is not a distribution-ready notice bundle.

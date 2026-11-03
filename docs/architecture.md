# Initial architecture (proposed)

## Boundary and data flow

Windows-only desktop application, Python 3.12+, local processing and local storage. No cloud OCR, remote uploads or telemetry are planned.

Image import -> immutable source reference and SHA-256 -> quality assessment -> derived preprocessing -> local OCR -> version-aware consistency checks -> explainable anomaly observations -> human review -> explicitly saved local case.

Every arrow above is a future implementation. No executable pipeline exists in this scaffold.

## Responsibilities

- `ui`: PySide6 views, case navigation, original/derived preview and review workflow. UI events call application services; CPU-heavy work executes outside the UI thread, supports cancellation and bounded resource use.
- `image_processing`: decode with size limits, quality signals, orientation and perspective correction; derived images never replace originals.
- `ocr`: local engine adapter; return text, bounding boxes, language, confidence and engine/model versions. OCR output is untrusted input.
- `document_validation`: explicitly supported country/version profiles and textual/MRZ consistency checks when applicable. Unknown versions remain unsupported, not fraudulent.
- `fraud_detection`: visible anomaly observations with location, rationale and uncertainty; no undocumented genuine/fake verdict or uncalibrated authenticity percentage.
- `domain`: future immutable contracts for case identifiers, provenance, observations, quality and review decisions; modules communicate through these contracts.
- `storage`: SQLite repositories and versioned migrations, parameterized queries, transaction boundaries and retention handling. SQLite is not encrypted by default.

## Planned persisted records

Case metadata, source hashes, optional explicitly retained source references, derived-artifact hashes, processing versions, profile version, OCR output, observations and examiner decisions. Keep machine observations distinct from examiner decisions. No schema or database is created yet.

## Windows packaging

Build on Windows for Windows using PyInstaller. Start with a directory bundle for inspection. Validate Qt plugins, native OpenCV libraries, Tesseract and language files on clean Windows 10/11 test machines. Code signing, installer format and update policy remain decisions for later development.

## Open decisions

Select initial countries/card versions using lawfully sourced reference material; select OCR languages and deployment assets; define calibrated quality thresholds; define storage/retention defaults and encryption needs; resolve and lock dependencies; choose project and Qt distribution licenses. These must be recorded before release claims.

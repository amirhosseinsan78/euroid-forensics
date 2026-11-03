# Architecture — MVP v0.1 desktop phase

## Implemented flow

`__main__` configures Qt and the per-user data path. `ui.main_window` snapshots input assets and per-side ROIs before creating a worker thread. Loading uses Pillow header checks and EXIF normalization, then immutable NumPy/OpenCV pixels. `services.analyze` invokes image quality heuristics and adds explicit inactive-stage results from OCR, MRZ, templates and fraud modules. The GUI presents a serializable report and optionally saves it through `storage.repository`.

Quality scores run on the selected crop (or full image), reduced to a maximum edge of 1600 pixels. Candidate coordinates map back to the oriented source image. The report stores the reduction scale, thresholds and analyzer version. Region changes invalidate results rather than displaying stale findings.

Worker cancellation is cooperative before/after bounded operations and between sides. A close request waits for worker completion; no thread is destroyed while native work is running. Loading failure preserves the previous valid input. Source files are never modified.

SQLite schema v1 contains `reports(id, created_at, payload)` with a JSON snapshot. `PRAGMA user_version` rejects unknown newer schemas. Saves use parameterized transactions; the same report ID is idempotent. Runtime data is outside the checkout; filenames and hashes, but no original paths or image bytes, are persisted. Saved history opens read-only snapshots, without reprocessing files.

All snapshots cross a strict schema-v1 validation boundary on save/load and again before HTML rendering. Only bounded built-in JSON types are accepted: no numeric-string or boolean coercion, non-finite metrics, unknown structural fields, unsupported statuses, duplicate sides/stages or invalid dimensions/ROIs. JSON payloads are limited to 1 MiB and duplicate keys/deeply malformed JSON are rejected. History metadata is validated separately. Every rendered dynamic value, including numbers and metric keys, is escaped; failures become controlled ValueError-family errors handled by the history UI. Validation checks structure, not cryptographic integrity of an editable local database.

Image loading retains one immutable BGR array per side. EXIF normalization updates only the decoded Pillow image in place. Opaque images bypass RGBA conversion; alpha inputs composite onto an RGB white surface without a second full RGBA result. The viewer borrows the BGR array into a temporary QImage and creates an independently owned QPixmap, avoiding full-size temporary RGB and copied QImage buffers. Loading is serialized by the existing worker gate while both sides can remain loaded. Full-resolution pixels and coordinate behavior are preserved; see docs/memory-evaluation.md.

The boundaries below describe the intended full MVP. Perspective rectification, OCR, official profiles, forensic anomaly models, encryption, retention controls and standalone packaging remain future work. The existing six issues remain open because this phase does not meet all of their acceptance criteria.

## Boundary and data flow

Windows-only desktop application, Python 3.12+, local processing and local storage. No cloud OCR, remote uploads or telemetry are planned.

Image import -> immutable source reference and SHA-256 -> quality assessment -> derived preprocessing -> local OCR -> version-aware consistency checks -> explainable anomaly observations -> human review -> explicitly saved local case.

Only import, quality assessment, human-readable review and optional result persistence are active. The remaining arrows describe future development.

## Responsibilities

- `ui`: PySide6 views, case navigation, original/derived preview and review workflow. UI events call application services; CPU-heavy work executes outside the UI thread, supports cancellation and bounded resource use.
- `image_processing`: decode with size limits, quality signals, orientation and perspective correction; derived images never replace originals.
- `ocr`: local engine adapter; return text, bounding boxes, language, confidence and engine/model versions. OCR output is untrusted input.
- `document_validation`: explicitly supported country/version profiles and textual/MRZ consistency checks when applicable. Unknown versions remain unsupported, not fraudulent.
- `fraud_detection`: visible anomaly observations with location, rationale and uncertainty; no undocumented genuine/fake verdict or uncalibrated authenticity percentage.
- `domain`: future immutable contracts for case identifiers, provenance, observations, quality and review decisions; modules communicate through these contracts.
- `storage`: SQLite repositories and versioned migrations, parameterized queries, transaction boundaries and retention handling. SQLite is not encrypted by default.

## Planned persisted records

Current snapshots store source filename/hash/dimensions, ROI, quality measurements, candidate boundary points, observation explanations/confidence, inactive stage statuses, analyzer/schema versions and timestamp. Future full cases may add OCR output, profile versions, derived artifacts and examiner decisions; machine observations must remain distinct from examiner decisions.

## Windows packaging

Build on Windows for Windows using PyInstaller. Start with a directory bundle for inspection. Validate Qt plugins, native OpenCV libraries, Tesseract and language files on clean Windows 10/11 test machines. Code signing, installer format and update policy remain decisions for later development.

## Open decisions

Select initial countries/card versions using lawfully sourced reference material; select OCR languages and deployment assets; define calibrated quality thresholds; define storage/retention defaults and encryption needs; resolve and lock dependencies; choose project and Qt distribution licenses. These must be recorded before release claims.

# MVP v0.1 backlog

Milestone: [MVP v0.1](https://github.com/amirhosseinsan78/euroid-forensics/milestone/1). No due date is assumed. The six existing issues are tracked in the [EuroID Forensics board](https://github.com/users/amirhosseinsan78/projects/1). The repository is Public; the board has its own access settings. [PR #7](https://github.com/amirhosseinsan78/euroid-forensics/pull/7) contains the current desktop phase and its review fixes.

Desktop phase progress (`feat/mvp-desktop-shell`): UI import/view/ROI/theme/review workflow, OpenCV quality heuristics, explicit SQLite snapshots and synthetic automated tests are implemented. OCR/MRZ/template/fraud interfaces are defined but inactive. No issue is automatically closed by this phase: perspective rectification, native OCR deployment, official profile coverage, evaluated anomaly detectors and standalone release validation still require follow-up under the existing issues.

| Workstream | GitHub issue |
| --- | --- |
| UI | [#1](https://github.com/amirhosseinsan78/euroid-forensics/issues/1) |
| Image Processing | [#2](https://github.com/amirhosseinsan78/euroid-forensics/issues/2) |
| OCR | [#3](https://github.com/amirhosseinsan78/euroid-forensics/issues/3) |
| Document Validation | [#4](https://github.com/amirhosseinsan78/euroid-forensics/issues/4) |
| Fraud Detection | [#5](https://github.com/amirhosseinsan78/euroid-forensics/issues/5) |
| Testing | [#6](https://github.com/amirhosseinsan78/euroid-forensics/issues/6) |

## UI

Title: [UI] Build local case review workflow

- [ ] Create PySide6 shell, image import, original/derived preview and observation panel.
- [ ] Show unsupported, inconclusive, error and cancellation states without blocking the UI.
- [ ] Make OCR and automated observations independently reviewable; avoid authenticity certification wording.

Acceptance: keyboard-accessible workflow, cancellation and clear uncertainty demonstrated on synthetic fixtures.

## Image Processing

Title: [Image Processing] Add image quality and preprocessing pipeline

- [ ] Bounded image decode, orientation, perspective and quality checks.
- [ ] Preserve original bytes; record source and derivative hashes and processing parameters.
- [ ] Return inconclusive for unusable inputs; record transformations.

Acceptance: synthetic skew, glare, blur, oversized and malformed inputs handled deterministically without modifying originals.

## OCR

Title: [OCR] Integrate offline Tesseract adapter

- [ ] Define OCR result contract with text, boxes, language, confidence and engine/model versions.
- [ ] Configure local Tesseract and selected language data, timeouts and missing-engine handling.
- [ ] Inventory redistributable engine/model assets and licenses.

Acceptance: offline extraction and error paths verified on synthetic multilingual fixtures; no data leaves device.

## Document Validation

Title: [Document Validation] Define supported profiles and consistency checks

- [ ] Select and document the first supported country/card versions and lawful reference sources.
- [ ] Add profile-aware field, date and MRZ consistency checks where applicable.
- [ ] Separate OCR uncertainty and unsupported versions from document anomalies.

Acceptance: supported/unsupported profile behavior documented; consistency results never imply genuine status.

## Fraud Detection

Title: [Fraud Detection] Add explainable visual anomaly observations

- [ ] Define observation contract: category, image region, evidence, rule/version and uncertainty.
- [ ] Select initial visible checks and thresholds using documented reference profiles.
- [ ] Define held-out evaluation, false positives/negatives and abstention reporting.

Acceptance: each observation is traceable and reviewable; no unvalidated accuracy claims or genuine/fake certification.

## Testing

Title: [Testing] Establish offline Windows MVP verification and packaging

- [ ] Set up unit, integration and UI tests using synthetic fixtures only.
- [ ] Verify SQLite persistence/migrations, transactions, retention and failure recovery once implemented.
- [ ] Resolve dependency lock, collect complete licenses/SBOM and prepare PyInstaller build.
- [ ] Smoke-test offline on clean Windows 10/11 with missing OCR assets and malformed images.

Acceptance: reproducible build, recorded environment, offline execution, provenance checks and limitation wording verified; no real personal data in CI.

## Milestone exit criteria

All six workstreams accepted; a documented supported subset works offline from import through human review and optional SQLite saving; Windows packaging checks pass; dependency obligations are reviewed; measured limitations are documented. This scaffold does not satisfy the implementation milestone.

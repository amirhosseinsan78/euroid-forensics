# Local data handling plan

Use synthetic, clearly non-valid fixtures in the repository. Do not upload real identity documents or personal OCR results to GitHub issues, CI logs or artifacts. Git ignore patterns are an aid, not a security boundary; review every staged change.

The GitHub repository is Public, including branches, PRs and Actions logs. This does not publish runtime SQLite files, which remain local and ignored. Board visibility is independent. Do not commit local databases or reports when contributing to the public repository.

Runtime reports use Qt AppLocalDataLocation outside the checkout, or an explicit `--db` path. Original file bytes are SHA-256 hashed before EXIF normalization; originals are not modified or copied into the database. Snapshot fields include filename, original hash, dimensions, ROI, metrics, findings, stage statuses and limits. Full original paths, image pixels and OCR text are not persisted in this phase. This is a provenance design, not a claim of legally sufficient chain of custody.

Save is explicit and idempotent per analysis ID. Opening history may initialize an empty database. No automatic retention/deletion/export or encryption is implemented; saved results remain until the owner manages the database. No logs containing image contents are generated. In-memory pixels live for the current workspace and are released when replaced/removed or the process exits. SQLite is not encrypted; use synthetic data in this phase.

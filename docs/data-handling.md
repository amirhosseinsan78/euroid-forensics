# Local data handling plan

Use synthetic, clearly non-valid fixtures in the repository. Do not upload real identity documents or personal OCR results to GitHub issues, CI logs or artifacts. Git ignore patterns are an aid, not a security boundary; review every staged change.

Future runtime case data belongs in a per-user application data directory outside the checkout. Preserve original files, record hashes before processing and track derived artifacts separately. This is a provenance design, not a claim of legally sufficient chain of custody.

Define explicit save, retention, deletion and export behavior before implementing persistence. Avoid personal data in logs; handle temporary images and process failures with bounded lifetime. SQLite does not provide encryption by default; choose protection requirements before using real case data. No storage, encryption or deletion features are implemented yet.

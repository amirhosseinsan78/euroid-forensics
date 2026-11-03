# Automated tests

Run `python -m pytest -q` in the installed development environment. The suite covers bounded decoding/EXIF/Unicode paths/transparency, quality and candidate geometry, ROI coordinates, cancellation and thread shutdown, SQLite snapshots/schema handling, both palettes and the complete synthetic GUI workflow. Fixtures are generated at runtime and contain no real identity information. Use `QT_QPA_PLATFORM=offscreen` for headless execution, then unset it before a visible GUI launch. See docs/validation.md for executed results.

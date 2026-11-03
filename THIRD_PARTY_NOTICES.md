# Preliminary dependency and license inventory

This is a planning inventory, not the complete notices required for redistribution. Exact resolved versions, transitive dependencies, native DLLs, OCR models, fonts and notices must be inventoried before shipping. No third-party source or binary is bundled in this scaffold.

| Component | Planned purpose | Upstream license / source |
| --- | --- | --- |
| Python | Runtime, including sqlite3 binding | [PSF and included notices](https://docs.python.org/3/license.html) |
| PySide6 / Qt | Desktop UI | LGPLv3/GPLv3/commercial options; exact module terms vary. [Qt licensing](https://www.qt.io/development/qt-framework/qt-licensing) |
| OpenCV 4.10+ | Image processing | Apache-2.0 for modern OpenCV; [upstream](https://opencv.org/license/) |
| opencv-python-headless | OpenCV wheels, without a second GUI toolkit | [Packaging license and bundled notices](https://github.com/opencv/opencv-python/blob/master/LICENSE.txt); inspect exact wheel contents |
| pytesseract | OCR wrapper | [Apache-2.0](https://github.com/madmaze/pytesseract) |
| Tesseract | Separate native OCR engine | [Apache-2.0](https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE); language assets require their own inventory |
| SQLite | Local database engine | [Public domain](https://sqlite.org/copyright.html) |
| PyInstaller | Windows executable build tooling | [GPL with distribution exception and some Apache-2.0 files](https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt) |
| pytest | Development testing | [MIT](https://github.com/pytest-dev/pytest/blob/main/LICENSE) |
| Ruff | Development linting | [MIT](https://github.com/astral-sh/ruff/blob/main/LICENSE) |
| setuptools | Build backend | [MIT](https://github.com/pypa/setuptools/blob/main/LICENSE) |

Before distribution, select and document the Qt licensing route and permitted modules, preserve notices and applicable source/relinking obligations, and evaluate the chosen PyInstaller bundle. The exception for PyInstaller does not remove obligations of bundled libraries. Produce a versioned dependency lock and SBOM from the actual Windows build, including Pillow, NumPy, Shiboken and other transitive components.

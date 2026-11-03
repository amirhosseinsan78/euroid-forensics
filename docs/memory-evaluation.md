# Two-image memory evaluation

Measured on 2026-11-03 on Windows 11 build 26300 x64 / Python 3.12.14 with the dependency versions in `requirements/windows-py312.constraints.txt`. The baseline is commit `78368b4`; the comparison is the PR #7 review fix. Fixtures are geometric synthetic images, without identity information.

## Method

`tools/benchmark_memory.py` generates two 6000 × 4000 (24 MP each) images in a parent process, then starts a fresh Qt offscreen child. The child retains both BGR arrays and both full-resolution Qt viewer pixmaps. It loads sides sequentially, matching the application's worker gate; both sides remain resident together. This does not claim two parallel decoder threads. Fixture generation does not inflate child peak usage.

Windows `GetProcessMemoryInfo` measures process peak working set, current working set and private commit, including native Pillow/OpenCV/Qt allocations. Python-only tracemalloc would miss much of this allocation. A baseline Git ref selects the original decoder and viewer; other imports and the two-image procedure remain the same.

From the installed repository development environment:

```powershell
.\.venv\Scripts\python.exe tools/benchmark_memory.py --directory ..\..\work\memory-fixtures --ref 78368b4 --scenario rgb
.\.venv\Scripts\python.exe tools/benchmark_memory.py --directory ..\..\work\memory-fixtures --scenario rgb
.\.venv\Scripts\python.exe tools/benchmark_memory.py --directory ..\..\work\memory-fixtures --ref 78368b4 --scenario rgba
.\.venv\Scripts\python.exe tools/benchmark_memory.py --directory ..\..\work\memory-fixtures --scenario rgba
```

Choose an intermediate directory outside the checkout. The baseline ref must be available in the local clone. This benchmark is manual, not part of the ordinary pytest suite or a machine-independent memory threshold.

## Representative measurements (MiB)

| Two retained 24 MP inputs | Baseline peak working set | Optimized peak working set | Peak reduction | Steady working set after second image |
| --- | ---: | ---: | ---: | ---: |
| Opaque RGB JPEGs | 734.4 | 460.0 | 37% | 390.9 → 390.9 |
| Half-transparent RGBA PNGs | 733.7 | 551.1 | 25% | 390.9 → 390.8 |

The two retained BGR arrays alone occupy 137.3 MiB. Private commit after loading both was approximately 720 MiB in both versions; this includes native reservations and is not the same as resident working set. Startup working set was about 65 MiB. These are individual measured runs, not universal guarantees; allocator caching, decoded formats, EXIF transforms, system pressure and real visible GPU-backed windows can differ. Replacing an existing side while retaining its previous valid image during decoding can require additional transient memory beyond this initial two-image scenario.

## Changes and remaining budget

- Avoid the default full-image EXIF copy for unrotated inputs; operate on the decoded in-memory Pillow image.
- Decode opaque images without an RGBA round trip. Alpha inputs still composite onto white, using fewer full-size intermediates.
- Construct the viewer QImage directly over the retained BGR array; QPixmap gets its own storage. Avoid temporary RGB and copied QImage buffers.
- Preserve full-resolution analysis, zoom and ROI pixel coordinates. The existing 25 MiB file / 24 MP / 12000-pixel-side limits and serialized loading remain in place.

Steady-state usage is intentionally not reduced by downsampling because full-resolution inspection is required. Low-memory machines may still reject very large inputs; clean Windows 10 and constrained-memory device testing remains a release validation task. No claim of universal low-memory compatibility is made.

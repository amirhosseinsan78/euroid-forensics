"""Measure Windows process memory with two retained full-size synthetic image views.

Run in an installed dev environment; fixtures and worker measurements are isolated
in a child process so fixture creation does not inflate the decoding high-water mark.
"""

import argparse
import ctypes
import importlib.util
import json
import os
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path


def memory_mib():
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t)
            for name in (
                "PeakWorkingSetSize",
                "WorkingSetSize",
                "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage",
                "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage",
                "PagefileUsage",
                "PeakPagefileUsage",
                "PrivateUsage",
            )
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(Counters),
        wintypes.DWORD,
    ]
    values = Counters()
    values.cb = ctypes.sizeof(values)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(values), values.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {
        key: round(getattr(values, field) / 1024**2, 1)
        for key, field in (
            ("peak_working_set_mib", "PeakWorkingSetSize"),
            ("working_set_mib", "WorkingSetSize"),
            ("private_commit_mib", "PrivateUsage"),
        )
    }


def reference_module(ref, path, name):
    source = subprocess.check_output(["git", "show", f"{ref}:{path}"], encoding="utf-8")
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(source, path, "exec"), module.__dict__)
    return module


def measure(args):
    from PySide6.QtWidgets import QApplication

    from euroid_forensics.image_processing.loading import load_image
    from euroid_forensics.ui.image_view import ImageView

    if args.ref:
        load_image = reference_module(
            args.ref, "src/euroid_forensics/image_processing/loading.py", "baseline_loading"
        ).load_image
        ImageView = reference_module(
            args.ref, "src/euroid_forensics/ui/image_view.py", "baseline_view"
        ).ImageView
    app = QApplication([])
    views = [ImageView(), ImageView()]
    result = {
        "ref": args.ref or "working-tree",
        "scenario": args.scenario,
        "baseline": memory_mib(),
        "stages": [],
    }
    assets = []
    suffix = ".png" if args.scenario == "rgba" else ".jpg"
    for index, view in enumerate(views):
        asset = load_image(args.directory / f"synthetic-{index}{suffix}")
        assets.append(asset)
        view.set_asset(asset)
        app.processEvents()
        result["stages"].append(memory_mib())
    assert sum(asset.bgr.nbytes for asset in assets) == 144_000_000
    result["retained_bgr_mib"] = round(144_000_000 / 1024**2, 1)
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--ref", help="Optional baseline Git ref, e.g. 78368b4")
    parser.add_argument("--scenario", choices=("rgb", "rgba"), default="rgb")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("This benchmark uses Windows process memory counters.")
    if args.worker:
        measure(args)
        return
    from PIL import Image, ImageDraw

    args.directory.mkdir(parents=True, exist_ok=True)
    for index in range(2):
        mode = "RGBA" if args.scenario == "rgba" else "RGB"
        color = (100, 130, 160, 128) if mode == "RGBA" else (100, 130, 160)
        with Image.new(mode, (6000, 4000), color) as fixture:
            draw = ImageDraw.Draw(fixture)
            draw.rectangle((300, 300, 5700, 3700), outline="white", width=20)
            suffix = ".png" if mode == "RGBA" else ".jpg"
            fixture.save(args.directory / f"synthetic-{index}{suffix}")
    command = [
        sys.executable,
        __file__,
        "--directory",
        str(args.directory.resolve()),
        "--scenario",
        args.scenario,
        "--worker",
    ]
    if args.ref:
        command += ["--ref", args.ref]
    environment = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    subprocess.run(command, env=environment, check=True)


if __name__ == "__main__":
    main()

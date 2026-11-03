"""Bounded local decoding with original-byte provenance and EXIF orientation."""

import hashlib
import io
import warnings
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 25 * 1024 * 1024
MAX_PIXELS = 24_000_000
MAX_DIMENSION = 12_000


@dataclass(frozen=True)
class ImageAsset:
    filename: str
    sha256: str
    bgr: np.ndarray

    @property
    def width(self) -> int:
        return self.bgr.shape[1]

    @property
    def height(self) -> int:
        return self.bgr.shape[0]


def decode_image(data: bytes, filename: str) -> ImageAsset:
    if Path(filename).suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise ValueError("Choose a JPG or PNG image.")
    if len(data) > MAX_BYTES:
        raise ValueError("Image exceeds the 25 MiB file limit.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.format not in {"JPEG", "PNG"}:
                    raise ValueError("File contents must be JPEG or PNG.")
                width, height = source.size
                if (
                    min(width, height) < 32
                    or max(width, height) > MAX_DIMENSION
                    or width * height > MAX_PIXELS
                ):
                    raise ValueError(
                        "Image must be 32+ pixels per side, ≤24 MP and ≤12000 per side."
                    )
                if getattr(source, "n_frames", 1) != 1:
                    raise ValueError("Animated images are not supported.")
                oriented = ImageOps.exif_transpose(source).convert("RGBA")
                # Explicit white compositing avoids interpreting invisible RGB as evidence.
                background = Image.new("RGBA", oriented.size, "white")
                rgb = np.asarray(Image.alpha_composite(background, oriented).convert("RGB"))
                bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValueError("Image is corrupt, unsupported or too large to decode safely.") from exc
    bgr.setflags(write=False)
    return ImageAsset(Path(filename).name, hashlib.sha256(data).hexdigest(), bgr)


def load_image(path: Path) -> ImageAsset:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Image exceeds the 25 MiB file limit.")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    return decode_image(data, path.name)

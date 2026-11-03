"""Purely geometric non-identity fixtures, generated locally without network access."""

import cv2
import numpy as np

from euroid_forensics.image_processing.loading import ImageAsset, decode_image


def demo_assets() -> dict[str, ImageAsset]:
    assets = {}
    for side in ("front", "back"):
        image = np.full((720, 1100, 3), (45, 52, 63), dtype=np.uint8)
        cv2.rectangle(image, (120, 90), (980, 630), (210, 220, 224), -1)
        cv2.rectangle(image, (140, 110), (960, 610), (80, 105, 125), 2)
        cv2.putText(
            image,
            "SYNTHETIC TEST / NOT VALID",
            (170, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (40, 55, 65),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            side.upper() + " - GEOMETRY ONLY",
            (170, 230),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (50, 65, 75),
            2,
            cv2.LINE_AA,
        )
        for y in range(300, 550, 38):
            cv2.line(image, (190, y), (900, y), (80, 110, 120), 3)
        if side == "back":
            image = cv2.GaussianBlur(image, (25, 25), 8)
        ok, encoded = cv2.imencode(".png", image)
        if not ok:
            raise RuntimeError("Synthetic image generation failed.")
        assets[side] = decode_image(encoded.tobytes(), f"synthetic-{side}.png")
    return assets

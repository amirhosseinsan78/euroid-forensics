import hashlib
import io

import numpy as np
import pytest
from PIL import Image

from euroid_forensics.image_processing import loading


def encoded(mode="RGB", size=(160, 100), color="gray", format="PNG", **kwargs):
    stream = io.BytesIO()
    Image.new(mode, size, color).save(stream, format=format, **kwargs)
    return stream.getvalue()


@pytest.mark.parametrize("format,suffix", [("PNG", ".PNG"), ("JPEG", ".jpg")])
def test_unicode_file_loading_preserves_original(tmp_path, format, suffix):
    data = encoded(format=format)
    path = tmp_path / ("نمونه بدون هویت" + suffix)
    path.write_bytes(data)
    image = loading.load_image(path)
    assert image.sha256 == hashlib.sha256(data).hexdigest()
    assert image.width == 160 and image.height == 100
    assert not image.bgr.flags.writeable
    assert path.read_bytes() == data


@pytest.mark.parametrize(
    "data,name",
    [
        (b"broken", "test.png"),
        (encoded(format="BMP"), "test.png"),
        (encoded(), "test.gif"),
        (encoded(size=(10, 10)), "tiny.png"),
    ],
)
def test_rejects_bad_inputs(data, name):
    with pytest.raises(ValueError):
        loading.decode_image(data, name)


def test_rejects_pixel_bomb_before_decode(monkeypatch):
    monkeypatch.setattr(loading, "MAX_PIXELS", 100)
    with pytest.raises(ValueError, match="24 MP"):
        loading.decode_image(encoded(), "large.png")


def test_rejects_large_file_before_read(tmp_path, monkeypatch):
    monkeypatch.setattr(loading, "MAX_BYTES", 10)
    path = tmp_path / "large.png"
    path.write_bytes(b"x" * 11)
    with pytest.raises(ValueError, match="25 MiB"):
        loading.load_image(path)
    with pytest.raises(ValueError, match="25 MiB"):
        loading.decode_image(b"x" * 11, "large.png")


def test_applies_exif_orientation_but_hashes_original():
    exif = Image.Exif()
    exif[274] = 6
    data = encoded(format="JPEG", exif=exif)
    image = loading.decode_image(data, "rotated.jpg")
    assert (image.width, image.height) == (100, 160)
    assert image.sha256 == hashlib.sha256(data).hexdigest()


def test_transparent_pixels_are_composited_on_white():
    image = loading.decode_image(encoded(mode="RGBA", color=(0, 0, 0, 0)), "clear.png")
    assert np.all(image.bgr == 255)


def test_rejects_animated_png():
    stream = io.BytesIO()
    Image.new("RGB", (100, 100), "red").save(
        stream,
        format="PNG",
        save_all=True,
        append_images=[Image.new("RGB", (100, 100), "blue")],
        duration=100,
    )
    with pytest.raises(ValueError, match="Animated"):
        loading.decode_image(stream.getvalue(), "animated.png")


@pytest.mark.parametrize(
    "mode,color",
    [("RGB", (12, 75, 203)), ("RGBA", (12, 75, 203, 128)), ("LA", (75, 128)), ("L", 75)],
)
def test_optimized_conversion_matches_white_composite(mode, color):
    data = encoded(mode=mode, color=color)
    with Image.open(io.BytesIO(data)) as source:
        expected = Image.alpha_composite(
            Image.new("RGBA", source.size, "white"), source.convert("RGBA")
        ).convert("RGB")
        expected_rgb = np.asarray(expected)
    image = loading.decode_image(data, "synthetic.png")
    np.testing.assert_array_equal(image.bgr[:, :, ::-1], expected_rgb)


def test_palette_transparency_is_preserved():
    source = Image.new("P", (100, 100), 0)
    source.putpalette([255, 0, 0] + [0] * 765)
    stream = io.BytesIO()
    source.save(stream, format="PNG", transparency=0)
    image = loading.decode_image(stream.getvalue(), "palette.png")
    assert np.all(image.bgr == 255)

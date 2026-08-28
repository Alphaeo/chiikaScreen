"""Screen capture."""

import mss
from PIL import Image

MAX_DIMENSION = 896


def capture_screen() -> Image.Image:
    """Grab the primary monitor and return it as a PIL image, downscaled
    so the vision model doesn't choke on a 4K screenshot."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    if max(img.size) > MAX_DIMENSION:
        scale = MAX_DIMENSION / max(img.size)
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)

    return img

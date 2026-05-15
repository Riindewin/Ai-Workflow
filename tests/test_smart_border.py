"""
Unit tests for SmartBorder.

Correctness properties:
  P1. Output is always a PIL Image
  P2. Output size always equals (width, height)
  P3. blur mode returns an RGB image
  P4. dominant mode fill colour is derived from the source image
  P5. normal mode uses the provided hex colour
  P6. Invalid colour string falls back to black without raising
"""

import pytest
from PIL import Image

from core.smart_border import SmartBorder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def red_image():
    """Solid red 50x50 image."""
    return Image.new("RGB", (50, 50), color=(255, 0, 0))


@pytest.fixture
def rgba_image():
    """RGBA image to test mode conversion robustness."""
    return Image.new("RGBA", (40, 40), color=(0, 128, 255, 200))


TARGET_W, TARGET_H = 200, 200


# ---------------------------------------------------------------------------
# P1 + P2 — output type and size
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["normal", "blur", "dominant"])
def test_output_is_image_with_correct_size(red_image, mode):
    """P1 + P2: result is a PIL Image of the requested size."""
    result = SmartBorder.build(red_image, mode, TARGET_W, TARGET_H, "#000000")
    assert isinstance(result, Image.Image), "P1"
    assert result.size == (TARGET_W, TARGET_H), "P2"


# ---------------------------------------------------------------------------
# P3 — blur mode returns RGB
# ---------------------------------------------------------------------------

def test_blur_mode_returns_rgb(red_image):
    """P3: blur background must be RGB."""
    result = SmartBorder.build(red_image, "blur", TARGET_W, TARGET_H, "#000000")
    assert result.mode == "RGB"


# ---------------------------------------------------------------------------
# P4 — dominant mode colour
# ---------------------------------------------------------------------------

def test_dominant_mode_uses_average_colour():
    """P4: dominant fill should be close to the image's average colour."""
    # Solid blue image → dominant colour should be approximately (0, 0, 255)
    blue = Image.new("RGB", (50, 50), color=(0, 0, 200))
    result = SmartBorder.build(blue, "dominant", 100, 100, "#ffffff")
    pixel = result.getpixel((50, 50))
    assert pixel[2] > 150, "Blue channel should dominate"
    assert pixel[0] < 50, "Red channel should be low"


# ---------------------------------------------------------------------------
# P5 — normal mode uses provided colour
# ---------------------------------------------------------------------------

def test_normal_mode_uses_provided_colour():
    """P5: normal mode background should match the hex colour."""
    img = Image.new("RGB", (10, 10), color=(128, 128, 128))
    result = SmartBorder.build(img, "normal", 100, 100, "#ff0000")
    pixel = result.getpixel((50, 50))
    assert pixel == (255, 0, 0), f"Expected red pixel, got {pixel}"


# ---------------------------------------------------------------------------
# P6 — invalid colour falls back gracefully
# ---------------------------------------------------------------------------

def test_invalid_colour_falls_back_to_black(red_image):
    """P6: invalid colour string must not raise — falls back to black."""
    result = SmartBorder.build(red_image, "normal", 100, 100, "not_a_colour")
    assert isinstance(result, Image.Image)
    pixel = result.getpixel((50, 50))
    assert pixel == (0, 0, 0), f"Expected black fallback, got {pixel}"


# ---------------------------------------------------------------------------
# RGBA source image
# ---------------------------------------------------------------------------

def test_dominant_mode_handles_rgba(rgba_image):
    """dominant mode must handle RGBA source without crashing."""
    result = SmartBorder.build(rgba_image, "dominant", 100, 100, "#000000")
    assert result.size == (100, 100)

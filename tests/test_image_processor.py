"""
Unit tests for utils/image_processor.py shared utilities.

Correctness properties:
  P1. fit_image preserves aspect ratio
  P2. fit_image output fits within (width, height)
  P3. compose_on_background returns an image of size (width, height)
  P4. make_preview returns an image no larger than max_size
  P5. fit_image paste coordinates are non-negative
"""

import pytest
from PIL import Image

from utils.image_processor import fit_image, compose_on_background, make_preview
from core.smart_border import SmartBorder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def landscape():
    """200x100 landscape image."""
    return Image.new("RGB", (200, 100), color=(255, 0, 0))


@pytest.fixture
def portrait():
    """100x200 portrait image."""
    return Image.new("RGB", (100, 200), color=(0, 255, 0))


@pytest.fixture
def square():
    """150x150 square image."""
    return Image.new("RGB", (150, 150), color=(0, 0, 255))


TARGET_W, TARGET_H = 300, 300


# ---------------------------------------------------------------------------
# P1 — aspect ratio preserved
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("img_fixture", ["landscape", "portrait", "square"])
def test_fit_image_preserves_aspect_ratio(request, img_fixture):
    """P1: resized image must have the same aspect ratio as the source."""
    img = request.getfixturevalue(img_fixture)
    resized, new_w, new_h, _, _ = fit_image(img, TARGET_W, TARGET_H)

    src_ratio = img.width / img.height
    out_ratio = new_w / new_h
    assert abs(src_ratio - out_ratio) < 0.01, (
        f"Aspect ratio mismatch: src={src_ratio:.3f}, out={out_ratio:.3f}"
    )


# ---------------------------------------------------------------------------
# P2 — output fits within target
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("img_fixture", ["landscape", "portrait", "square"])
def test_fit_image_fits_within_target(request, img_fixture):
    """P2: resized dimensions must not exceed (width, height)."""
    img = request.getfixturevalue(img_fixture)
    _, new_w, new_h, _, _ = fit_image(img, TARGET_W, TARGET_H)
    assert new_w <= TARGET_W
    assert new_h <= TARGET_H


# ---------------------------------------------------------------------------
# P3 — compose_on_background returns correct size
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("img_fixture", ["landscape", "portrait", "square"])
def test_compose_on_background_size(request, img_fixture):
    """P3: composed image must be exactly (width, height)."""
    img = request.getfixturevalue(img_fixture)
    bg = SmartBorder.build(img, "normal", TARGET_W, TARGET_H, "#000000")
    result = compose_on_background(img, bg, TARGET_W, TARGET_H)
    assert result.size == (TARGET_W, TARGET_H)


# ---------------------------------------------------------------------------
# P4 — make_preview respects max_size
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("max_size", [(700, 600), (400, 300), (100, 100)])
def test_make_preview_respects_max_size(square, max_size):
    """P4: preview thumbnail must not exceed max_size in either dimension."""
    bg = SmartBorder.build(square, "normal", TARGET_W, TARGET_H, "#000000")
    composed = compose_on_background(square, bg, TARGET_W, TARGET_H)
    preview = make_preview(composed, max_size=max_size)
    assert preview.width <= max_size[0]
    assert preview.height <= max_size[1]


# ---------------------------------------------------------------------------
# P5 — paste coordinates are non-negative
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("img_fixture", ["landscape", "portrait", "square"])
def test_fit_image_paste_coords_non_negative(request, img_fixture):
    """P5: paste coordinates (x, y) must always be >= 0."""
    img = request.getfixturevalue(img_fixture)
    _, _, _, x, y = fit_image(img, TARGET_W, TARGET_H)
    assert x >= 0, f"x={x} is negative"
    assert y >= 0, f"y={y} is negative"

"""
Unit tests for AIEngine.

Property-based correctness properties:
  P1. Output dimensions = input dimensions * scale_factor (rounded down)
  P2. Output is a PIL Image
  P3. Invalid scale_factor raises ValueError
  P4. Unknown mode raises ValueError
  P5. set_mode ignores unknown modes (mode stays unchanged)
"""

import pytest
from PIL import Image

from core.ai_engine import AIEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def small_rgb():
    """100x80 RGB test image."""
    return Image.new("RGB", (100, 80), color=(128, 64, 32))


@pytest.fixture
def engine_low():
    return AIEngine(mode="low")


@pytest.fixture
def engine_balanced():
    return AIEngine(mode="balanced")


@pytest.fixture
def engine_ultra():
    return AIEngine(mode="ultra")


# ---------------------------------------------------------------------------
# P1 + P2 — output size and type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["low", "balanced", "ultra"])
@pytest.mark.parametrize("scale", [1.0, 1.5, 2.0, 3.0])
def test_upscale_output_size(small_rgb, mode, scale):
    """P1 + P2: output is a PIL Image with correct dimensions."""
    engine = AIEngine(mode=mode)
    result = engine.upscale(small_rgb, scale_factor=scale)

    assert isinstance(result, Image.Image), "P2: result must be a PIL Image"
    expected_w = int(small_rgb.width * scale)
    expected_h = int(small_rgb.height * scale)
    # Allow ±1 pixel tolerance due to integer rounding in resize chains
    assert abs(result.width  - expected_w) <= 1, (
        f"P1: expected width {expected_w}, got {result.width}"
    )
    assert abs(result.height - expected_h) <= 1, (
        f"P1: expected height {expected_h}, got {result.height}"
    )


# ---------------------------------------------------------------------------
# P3 — invalid scale_factor
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_scale", [0, -1.0, -0.5])
def test_upscale_invalid_scale(engine_low, small_rgb, bad_scale):
    """P3: non-positive scale_factor must raise ValueError."""
    with pytest.raises(ValueError):
        engine_low.upscale(small_rgb, scale_factor=bad_scale)


# ---------------------------------------------------------------------------
# P4 — unknown mode at construction falls back to default
# ---------------------------------------------------------------------------

def test_unknown_mode_falls_back_to_default():
    """P4: constructing with an unknown mode falls back to 'low'."""
    engine = AIEngine(mode="nonexistent")
    assert engine.get_mode() == "low"


# ---------------------------------------------------------------------------
# P5 — set_mode ignores unknown values
# ---------------------------------------------------------------------------

def test_set_mode_ignores_unknown(engine_low):
    """P5: set_mode with an unknown value leaves mode unchanged."""
    engine_low.set_mode("turbo_ultra_max")
    assert engine_low.get_mode() == "low"


def test_set_mode_accepts_valid(engine_low):
    engine_low.set_mode("balanced")
    assert engine_low.get_mode() == "balanced"


# ---------------------------------------------------------------------------
# process() dispatcher
# ---------------------------------------------------------------------------

def test_process_upscale(engine_low, small_rgb):
    result = engine_low.process(small_rgb, "upscale", scale_factor=2.0)
    # Allow ±1 pixel tolerance
    assert abs(result.width  - 200) <= 1
    assert abs(result.height - 160) <= 1


def test_process_unknown_task(engine_low, small_rgb):
    with pytest.raises(NotImplementedError):
        engine_low.process(small_rgb, "magic_enhance")


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------

def test_is_available(engine_low):
    assert engine_low.is_available() is True

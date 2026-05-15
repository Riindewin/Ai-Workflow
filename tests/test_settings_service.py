"""
Unit tests for SettingsService.

Correctness properties:
  P1. load() always returns a dict (never raises)
  P2. load() returns defaults when file is missing
  P3. load() returns defaults when file is malformed JSON
  P4. load() merges file values with defaults (no key is ever missing)
  P5. save() persists data that load() can read back
  P6. save() returns False on write failure (read-only path)
"""

import json
import os
import pytest

from services.settings_service import SettingsService, DEFAULTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_service(tmp_path, filename="settings.json"):
    path = str(tmp_path / filename)
    return SettingsService(path=path), path


# ---------------------------------------------------------------------------
# P1 — load always returns a dict
# ---------------------------------------------------------------------------

def test_load_returns_dict_when_file_missing(tmp_path):
    """P1: load() must return a dict even when the file does not exist."""
    svc, _ = make_service(tmp_path, "nonexistent.json")
    result = svc.load()
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# P2 — defaults when file is missing
# ---------------------------------------------------------------------------

def test_load_returns_defaults_when_missing(tmp_path):
    """P2: all default keys must be present when file is absent."""
    svc, _ = make_service(tmp_path, "nonexistent.json")
    result = svc.load()
    for key in DEFAULTS:
        assert key in result, f"Missing default key: {key}"


# ---------------------------------------------------------------------------
# P3 — defaults when file is malformed
# ---------------------------------------------------------------------------

def test_load_returns_defaults_on_malformed_json(tmp_path):
    """P3: malformed JSON must not raise — defaults are returned."""
    svc, path = make_service(tmp_path)
    with open(path, "w") as f:
        f.write("{ this is not valid json }")

    result = svc.load()
    assert isinstance(result, dict)
    for key in DEFAULTS:
        assert key in result


# ---------------------------------------------------------------------------
# P4 — merge: no key is ever missing
# ---------------------------------------------------------------------------

def test_load_merges_partial_file_with_defaults(tmp_path):
    """P4: partial settings file must be merged with defaults."""
    svc, path = make_service(tmp_path)
    partial = {"dark_mode": False, "quality": 80}
    with open(path, "w") as f:
        json.dump(partial, f)

    result = svc.load()
    assert result["dark_mode"] is False
    assert result["quality"] == 80
    # All other default keys must still be present
    for key in DEFAULTS:
        assert key in result


# ---------------------------------------------------------------------------
# P5 — round-trip: save then load
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    """P5: data saved by save() must be readable by load()."""
    svc, _ = make_service(tmp_path)
    data = {**DEFAULTS, "dark_mode": False, "quality": 42}
    svc.save(data)
    result = svc.load()
    assert result["dark_mode"] is False
    assert result["quality"] == 42


# ---------------------------------------------------------------------------
# P6 — save returns False on failure
# ---------------------------------------------------------------------------

def test_save_returns_false_on_failure(tmp_path):
    """P6: save() must return False when the path is not writable."""
    # Point to a directory path (cannot write a file over a directory)
    svc = SettingsService(path=str(tmp_path))
    result = svc.save({"key": "value"})
    assert result is False

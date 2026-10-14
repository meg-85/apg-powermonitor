"""Tests for the HA-independent API parsing logic."""

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

# Load api.py directly so the test does not need Home Assistant installed.
_spec = importlib.util.spec_from_file_location(
    "apg_api", ROOT / "custom_components" / "apg_powermonitor" / "api.py"
)
api = importlib.util.module_from_spec(_spec)
sys.modules["apg_api"] = api  # dataclasses need the module registered
_spec.loader.exec_module(api)

PAYLOAD = json.loads((Path(__file__).parent / "fixtures" / "peak_hour_status.json").read_text())


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_parse_basics():
    data = api.parse_peak_hour_status(PAYLOAD)
    assert data.default_status == "1"
    assert data.first_utc == utc(2026, 10, 13, 22)
    assert data.last_utc == utc(2026, 10, 18, 22)


def test_is_peak():
    data = api.parse_peak_hour_status(PAYLOAD)
    assert data.is_peak(utc(2026, 10, 14, 14, 28)) is True    # Wed 16:28 Vienna
    assert data.is_peak(utc(2026, 10, 15, 10, 30)) is False   # Thu 12:30 Vienna
    assert data.is_peak(utc(2026, 10, 13, 21, 59)) is None    # before forecast
    assert data.is_peak(utc(2026, 10, 18, 23, 0)) is None     # after forecast


def test_periods_are_merged():
    data = api.parse_peak_hour_status(PAYLOAD)
    first = data.periods[0]
    assert first.start == utc(2026, 10, 13, 22)
    assert first.end == utc(2026, 10, 15, 9)  # Thu 11:00 Vienna
    nxt = data.next_period(utc(2026, 10, 14, 14))
    assert nxt.start == utc(2026, 10, 15, 13)  # Thu 15:00 Vienna


def test_current_or_next_period():
    data = api.parse_peak_hour_status(PAYLOAD)
    in_peak = data.current_or_next_period(utc(2026, 10, 14, 14))
    assert in_peak.start == utc(2026, 10, 13, 22)
    gap = data.current_or_next_period(utc(2026, 10, 15, 10))
    assert gap.start == utc(2026, 10, 15, 13)


def test_peak_hours_between():
    data = api.parse_peak_hour_status(PAYLOAD)
    # Wed 14.10. local day = 13.10. 22:00Z .. 14.10. 22:00Z: all 24 hours peak
    assert data.peak_hours_between(utc(2026, 10, 13, 22), utc(2026, 10, 14, 22)) == 24
    # Thu 15.10.: 4 free hours (11-15 Vienna)
    assert data.peak_hours_between(utc(2026, 10, 14, 22), utc(2026, 10, 15, 22)) == 20
    # Partially outside the forecast -> unknown
    assert data.peak_hours_between(utc(2026, 10, 18, 22), utc(2026, 10, 19, 22)) is None

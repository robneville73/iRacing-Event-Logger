"""Unit tests for event detectors with mocked SDK data."""

import pytest

from iracing_event_logger.detectors import (
    check_lap_complete,
    check_pit,
    check_position_changes,
    _current_lap,
)
from iracing_event_logger.events import LAP_COMPLETE, PIT_ENTRY, PIT_EXIT, PASS, GOT_PASSED


class MockIR:
    """Minimal SDK-like object for testing."""

    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data.get(key)


def test_lap_complete_first_lap():
    """First lap completion: prev_lap_completed was 0, now 1."""
    ir = MockIR({
        "SessionTime": 100.0,
        "CarIdxLapCompleted": [0] * 64,
        "CarIdxLastLapTime": [0.0] * 64,
        "CarIdxPosition": [1] * 64,
    })
    ir._data["CarIdxLapCompleted"][2] = 1
    ir._data["CarIdxLastLapTime"][2] = 92.5
    ir._data["CarIdxPosition"][2] = 1
    ev, new_prev = check_lap_complete(ir, 2, 0, None)
    assert ev is not None
    assert ev["type"] == LAP_COMPLETE
    assert ev["lap"] == 1
    assert ev["session_time"] == 100.0
    assert ev.get("lap_time") == 92.5
    assert new_prev == 1


def test_lap_complete_no_change():
    """No lap completed: prev and current both 1."""
    ir = MockIR({
        "SessionTime": 100.0,
        "CarIdxLapCompleted": [1] * 64,
        "CarIdxLastLapTime": [92.0] * 64,
        "CarIdxPosition": [1] * 64,
    })
    ev, new_prev = check_lap_complete(ir, 2, 1, None)
    assert ev is None
    assert new_prev == 1


def test_pit_entry():
    """Transition off pit -> on pit."""
    ir = MockIR({
        "SessionTime": 200.0,
        "CarIdxOnPitRoad": [False] * 64,
        "CarIdxPosition": [5] * 64,
        "CarIdxLapDistPct": [0.5] * 64,
    })
    ir._data["CarIdxOnPitRoad"][3] = True
    events, on_now = check_pit(ir, 3, False, 2, None)
    assert len(events) == 1
    assert events[0]["type"] == PIT_ENTRY
    assert events[0]["session_time"] == 200.0
    assert on_now is True


def test_pit_exit():
    """Transition on pit -> off pit."""
    ir = MockIR({
        "SessionTime": 250.0,
        "CarIdxOnPitRoad": [True] * 64,
        "CarIdxPosition": [8] * 64,
        "CarIdxLapDistPct": [0.1] * 64,
    })
    ir._data["CarIdxOnPitRoad"][3] = False
    events, on_now = check_pit(ir, 3, True, 3, None)
    assert len(events) == 1
    assert events[0]["type"] == PIT_EXIT
    assert on_now is False


def test_position_pass():
    """Focus car position 4 -> 3: we passed someone (car in position 4 is the one we passed)."""
    ir = MockIR({
        "SessionTime": 150.0,
        "CarIdxPosition": [0, 1, 2, 3, 4, 5, 0, 0],
    })
    driver_info = {
        "Drivers": [
            {"CarIdx": 0, "CarNumber": "0", "UserName": "A"},
            {"CarIdx": 1, "CarNumber": "1", "UserName": "B"},
            {"CarIdx": 2, "CarNumber": "2", "UserName": "C"},
            {"CarIdx": 3, "CarNumber": "4", "UserName": "Focus"},
            {"CarIdx": 4, "CarNumber": "12", "UserName": "Passed"},
        ],
    }
    events, new_pos = check_position_changes(ir, 3, 4, driver_info, 2, None)
    assert new_pos == 3
    pass_ev = [e for e in events if e["type"] == PASS]
    assert len(pass_ev) == 1
    assert pass_ev[0]["new_position"] == 3
    assert pass_ev[0]["old_position"] == 4
    assert pass_ev[0]["passed_car_number"] == "12"


def test_position_got_passed():
    """Focus car position 2 -> 3: we got passed (passer took position 2)."""
    ir = MockIR({
        "SessionTime": 160.0,
        "CarIdxPosition": [0, 1, 2, 3, 4, 5],
    })
    driver_info = {
        "Drivers": [
            {"CarIdx": 0, "CarNumber": "0", "UserName": "A"},
            {"CarIdx": 1, "CarNumber": "1", "UserName": "B"},
            {"CarIdx": 2, "CarNumber": "7", "UserName": "Passer"},
            {"CarIdx": 3, "CarNumber": "5", "UserName": "Focus"},
        ],
    }
    events, new_pos = check_position_changes(ir, 3, 2, driver_info, 2, None)
    assert new_pos == 3
    got_ev = [e for e in events if e["type"] == GOT_PASSED]
    assert len(got_ev) == 1
    assert got_ev[0]["new_position"] == 3
    assert got_ev[0]["old_position"] == 2
    assert got_ev[0]["by_car_number"] == "7"


def test_current_lap():
    """_current_lap from CarIdxLapCompleted."""
    ir = MockIR({"CarIdxLapCompleted": [0, 0, 2, 0]})
    assert _current_lap(ir, 2) == 3
    assert _current_lap(ir, 0) == 1

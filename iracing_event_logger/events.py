"""Event type names and payload typing for the JSON log."""

from typing import Any, Dict

# Event type string constants (must match plan section 5.2)
LAP_COMPLETE = "lap_complete"
PASS = "pass"
GOT_PASSED = "got_passed"
PIT_ENTRY = "pit_entry"
PIT_EXIT = "pit_exit"
PIT_STOP_COMPLETE = "pit_stop_complete"
INCIDENT = "incident"
CLOSE_BATTLE = "close_battle"
DRIVER_CHANGE = "driver_change"
GAP_CLOSED = "gap_closed"
GAP_OPENED = "gap_opened"

ALL_TYPES = [
    LAP_COMPLETE,
    PASS,
    GOT_PASSED,
    PIT_ENTRY,
    PIT_EXIT,
    PIT_STOP_COMPLETE,
    INCIDENT,
    CLOSE_BATTLE,
    DRIVER_CHANGE,
    GAP_CLOSED,
    GAP_OPENED,
]


def base_event(
    event_type: str,
    session_time: float,
    lap: int,
    event_id: Any = None,
    replay_frame: Any = None,
) -> Dict[str, Any]:
    """Build event dict with common fields (type, session_time, lap)."""
    out: Dict[str, Any] = {
        "type": event_type,
        "session_time": session_time,
        "lap": lap,
    }
    if event_id is not None:
        out["id"] = event_id
    if replay_frame is not None:
        out["replay_frame"] = replay_frame
    return out

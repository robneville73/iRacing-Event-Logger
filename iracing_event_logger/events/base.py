"""Shared event builder and event type registry."""

from typing import Any, Dict

from . import (
    close_battle,
    driver_change,
    gap_closed,
    gap_opened,
    got_passed,
    incident,
    lap_complete,
    pass_event,
    pit_entry,
    pit_exit,
    pit_stop_complete,
)

# Re-export all type constants for convenience
LAP_COMPLETE = lap_complete.LAP_COMPLETE
PASS = pass_event.PASS
GOT_PASSED = got_passed.GOT_PASSED
PIT_ENTRY = pit_entry.PIT_ENTRY
PIT_EXIT = pit_exit.PIT_EXIT
PIT_STOP_COMPLETE = pit_stop_complete.PIT_STOP_COMPLETE
INCIDENT = incident.INCIDENT
CLOSE_BATTLE = close_battle.CLOSE_BATTLE
DRIVER_CHANGE = driver_change.DRIVER_CHANGE
GAP_CLOSED = gap_closed.GAP_CLOSED
GAP_OPENED = gap_opened.GAP_OPENED

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

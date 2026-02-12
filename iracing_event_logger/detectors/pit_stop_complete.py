"""Detect pit stop complete (player car, pit service status -> complete)."""

from typing import Any, Dict, List, Optional, Tuple

from ..events import PIT_STOP_COMPLETE, base_event
from .common import ir_get, replay_frame, session_time


def check_pit_stop_complete(
    ir: Any,
    focus_idx: int,
    player_car_idx: Optional[int],
    prev_pit_sv_status: Optional[int],
    pit_entry_session_time: Optional[float],
    current_lap: int,
    event_types_enabled: Optional[List[str]] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    """
    When focus car is player and pit service status transitions to complete (2), emit event.
    Returns (event or None, current status).
    """
    if event_types_enabled is not None and PIT_STOP_COMPLETE not in event_types_enabled:
        status = ir_get(ir, "PlayerCarPitSvStatus")
        return (None, status if status is not None else prev_pit_sv_status)
    if focus_idx != player_car_idx:
        return (None, prev_pit_sv_status)
    status = ir_get(ir, "PlayerCarPitSvStatus")
    if status is None:
        return (None, prev_pit_sv_status)
    status = int(status)
    if status == 2 and (prev_pit_sv_status is None or prev_pit_sv_status != 2):
        session_time_val = session_time(ir)
        ev = base_event(
            PIT_STOP_COMPLETE,
            session_time_val,
            current_lap,
            replay_frame=replay_frame(ir),
        )
        if pit_entry_session_time is not None:
            ev["pit_duration"] = round(session_time_val - pit_entry_session_time, 2)
        return (ev, status)
    return (None, status)

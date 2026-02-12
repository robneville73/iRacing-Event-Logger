"""Detect incident (PlayerCarMyIncidentCount increase for focus/player car)."""

from typing import Any, Dict, List, Optional, Tuple

from ..events import INCIDENT, base_event
from .common import focus_val, ir_get, replay_frame, session_time


def check_incident(
    ir: Any,
    focus_idx: int,
    player_car_idx: Optional[int],
    prev_incident_count: Optional[int],
    current_lap: int,
    event_types_enabled: Optional[List[str]] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    """
    When focus is player and PlayerCarMyIncidentCount increases, emit incident.
    Returns (event or None, updated prev_incident_count).
    """
    if event_types_enabled is not None and INCIDENT not in event_types_enabled:
        cnt = (
            ir_get(ir, "PlayerCarMyIncidentCount")
            if focus_idx == player_car_idx
            else None
        )
        return (None, cnt if cnt is not None else prev_incident_count)
    if focus_idx != player_car_idx:
        return (None, prev_incident_count)
    count = ir_get(ir, "PlayerCarMyIncidentCount")
    if count is None:
        return (None, prev_incident_count)
    count = int(count)
    prev = prev_incident_count if prev_incident_count is not None else 0
    if count > prev:
        session_time_val = session_time(ir)
        ev = base_event(
            INCIDENT, session_time_val, current_lap, replay_frame=replay_frame(ir)
        )
        ev["incident_count"] = count
        flags = ir_get(ir, "PlayerIncidents")
        if flags is not None:
            ev["flags"] = int(flags)
        surf = focus_val(ir, "CarIdxTrackSurface", focus_idx)
        if surf is not None:
            ev["track_surface"] = int(surf)
        ev["kind"] = "unknown"
        return (ev, count)
    return (None, count)

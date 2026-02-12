"""Detect pit_entry (entering pit road) and pit_exit (leaving pit road)."""

from typing import Any, Dict, List, Optional, Tuple

from ..events import PIT_ENTRY, PIT_EXIT, base_event
from .common import focus_val, replay_frame, session_time


def check_pit(
    ir: Any,
    focus_idx: int,
    prev_on_pit_road: Optional[bool],
    current_lap_val: int,
    event_types_enabled: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Detect pit_entry (false->true) and pit_exit (true->false).
    Returns (list of events, updated prev_on_pit_road).
    """
    events: List[Dict[str, Any]] = []
    on_now = focus_val(ir, "CarIdxOnPitRoad", focus_idx)
    if on_now is None:
        return (events, prev_on_pit_road if prev_on_pit_road is not None else False)
    on_now = bool(on_now)
    prev = prev_on_pit_road
    session_time_val = session_time(ir)
    if prev is not None:
        if not prev and on_now and (
            event_types_enabled is None or PIT_ENTRY in event_types_enabled
        ):
            ev = base_event(
                PIT_ENTRY, session_time_val, current_lap_val, replay_frame=replay_frame(ir)
            )
            pos = focus_val(ir, "CarIdxPosition", focus_idx)
            if pos is not None:
                ev["position"] = int(pos)
            lap_pct = focus_val(ir, "CarIdxLapDistPct", focus_idx)
            if lap_pct is not None and 0 <= float(lap_pct) <= 1:
                ev["lap_pct"] = float(lap_pct)
            events.append(ev)
        if prev and not on_now and (
            event_types_enabled is None or PIT_EXIT in event_types_enabled
        ):
            ev = base_event(
                PIT_EXIT, session_time_val, current_lap_val, replay_frame=replay_frame(ir)
            )
            pos = focus_val(ir, "CarIdxPosition", focus_idx)
            if pos is not None:
                ev["position"] = int(pos)
            lap_pct = focus_val(ir, "CarIdxLapDistPct", focus_idx)
            if lap_pct is not None and 0 <= float(lap_pct) <= 1:
                ev["lap_pct"] = float(lap_pct)
            events.append(ev)
    return (events, on_now)

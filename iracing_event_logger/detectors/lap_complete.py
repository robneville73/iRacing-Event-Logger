"""Detect lap completion (CarIdxLapCompleted increase)."""

from typing import Any, Dict, List, Optional, Tuple

from ..events import LAP_COMPLETE, base_event
from .common import current_lap, focus_val, replay_frame, session_time


def check_lap_complete(
    ir: Any,
    focus_idx: int,
    prev_lap_completed: Optional[int],
    event_types_enabled: Optional[List[str]] = None,
) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    If CarIdxLapCompleted increased, return a lap_complete event and new prev value.
    Returns (event_dict or None, updated prev_lap_completed).
    """
    if event_types_enabled is not None and LAP_COMPLETE not in event_types_enabled:
        current = focus_val(ir, "CarIdxLapCompleted", focus_idx)
        return (None, current if current is not None else prev_lap_completed)
    current = focus_val(ir, "CarIdxLapCompleted", focus_idx)
    if current is None:
        return (None, prev_lap_completed)
    prev = -1 if prev_lap_completed is None else prev_lap_completed
    if int(current) > prev and prev >= 0:
        lap = int(current)
        session_time_val = session_time(ir)
        lap_time = focus_val(ir, "CarIdxLastLapTime", focus_idx)
        position = focus_val(ir, "CarIdxPosition", focus_idx)
        class_pos = focus_val(ir, "CarIdxClassPosition", focus_idx)
        ev = base_event(LAP_COMPLETE, session_time_val, lap, replay_frame=replay_frame(ir))
        if lap_time is not None and float(lap_time) > 0:
            ev["lap_time"] = float(lap_time)
        if position is not None:
            ev["position"] = int(position)
        if class_pos is not None:
            ev["class_position"] = int(class_pos)
        return (ev, int(current))
    return (None, int(current))

"""Detect pass (gained position) and got_passed (lost position)."""

from typing import Any, Dict, List, Optional, Tuple

from ..events import GOT_PASSED, PASS, base_event
from ..sdk_wrapper import car_number_and_name, get_driver_by_car_idx
from .common import car_idx_at_position, focus_val, ir_get, replay_frame, session_time


def check_position_changes(
    ir: Any,
    focus_idx: int,
    prev_position: Optional[int],
    driver_info: Any,
    current_lap: int,
    event_types_enabled: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Detect pass (we gained position) or got_passed (we lost position).
    Returns (list of events, updated prev_position).
    """
    events: List[Dict[str, Any]] = []
    pos_arr = ir_get(ir, "CarIdxPosition")
    if not isinstance(pos_arr, (list, tuple)) or focus_idx >= len(pos_arr):
        return (events, prev_position or 0)
    new_pos = int(pos_arr[focus_idx]) if pos_arr[focus_idx] is not None else None
    if new_pos is None or new_pos <= 0:
        return (events, prev_position or 0)
    session_time_val = session_time(ir)
    prev = prev_position
    if prev is not None and prev > 0 and new_pos != prev:
        if new_pos < prev and PASS in (event_types_enabled or [PASS]):
            if event_types_enabled is None or PASS in event_types_enabled:
                other_idx = car_idx_at_position(ir, prev)
                num, name = (
                    car_number_and_name(get_driver_by_car_idx(driver_info, other_idx))
                    if other_idx is not None
                    else ("", "")
                )
                ev = base_event(PASS, session_time_val, current_lap, replay_frame=replay_frame(ir))
                ev["passed_car_number"] = num or "?"
                ev["new_position"] = new_pos
                if other_idx is not None:
                    ev["passed_car_idx"] = other_idx
                if name:
                    ev["passed_driver_name"] = name
                ev["old_position"] = prev
                class_pos = focus_val(ir, "CarIdxClassPosition", focus_idx)
                if class_pos is not None:
                    ev["class_position"] = int(class_pos)
                events.append(ev)
        if new_pos > prev and GOT_PASSED in (event_types_enabled or [GOT_PASSED]):
            if event_types_enabled is None or GOT_PASSED in event_types_enabled:
                other_idx = car_idx_at_position(ir, prev)
                num, name = (
                    car_number_and_name(get_driver_by_car_idx(driver_info, other_idx))
                    if other_idx is not None
                    else ("", "")
                )
                ev = base_event(
                    GOT_PASSED, session_time_val, current_lap, replay_frame=replay_frame(ir)
                )
                ev["by_car_number"] = num or "?"
                ev["new_position"] = new_pos
                if other_idx is not None:
                    ev["by_car_idx"] = other_idx
                if name:
                    ev["by_driver_name"] = name
                ev["old_position"] = prev
                class_pos = focus_val(ir, "CarIdxClassPosition", focus_idx)
                if class_pos is not None:
                    ev["class_position"] = int(class_pos)
                events.append(ev)
    return (events, new_pos)

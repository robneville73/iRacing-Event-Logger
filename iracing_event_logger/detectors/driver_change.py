"""Detect driver change (DriverInfo for focus car changed, e.g. UserName)."""

from typing import Any, Dict, List, Optional

from ..events import DRIVER_CHANGE, base_event
from ..sdk_wrapper import car_number_and_name, get_driver_by_car_idx


def check_driver_change(
    driver_info_current: Any,
    driver_info_previous: Any,
    focus_idx: int,
    session_time: float,
    current_lap: int,
    event_types_enabled: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    If DriverInfo for focus car changed (e.g. UserName), emit driver_change.
    """
    if event_types_enabled is not None and DRIVER_CHANGE not in event_types_enabled:
        return None
    if not driver_info_current or not driver_info_previous:
        return None
    prev_driver = get_driver_by_car_idx(driver_info_previous, focus_idx)
    curr_driver = get_driver_by_car_idx(driver_info_current, focus_idx)
    if not curr_driver:
        return None
    _, curr_name = car_number_and_name(curr_driver)
    _, prev_name = (
        car_number_and_name(prev_driver) if prev_driver else ("", "")
    )
    if prev_name != curr_name and (curr_name or prev_name):
        ev = base_event(DRIVER_CHANGE, session_time, current_lap)
        ev["current_driver_name"] = curr_name
        ev["previous_driver_name"] = prev_name
        ev["direction"] = "in"
        return ev
    return None

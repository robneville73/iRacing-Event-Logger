"""Event detection: compare current telemetry/session to previous state and emit events."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .events import (
    CLOSE_BATTLE,
    GOT_PASSED,
    INCIDENT,
    LAP_COMPLETE,
    PASS,
    PIT_ENTRY,
    PIT_EXIT,
    PIT_STOP_COMPLETE,
    base_event,
)
from .sdk_wrapper import get_driver_by_car_idx, car_number_and_name

logger = logging.getLogger(__name__)


def _ir_get(ir: Any, key: str, default: Any = None) -> Any:
    """Safe read from SDK (no .get method)."""
    if not ir:
        return default
    try:
        v = ir[key]
        return v if v is not None else default
    except (KeyError, TypeError, IndexError):
        return default


def _session_time(ir: Any) -> float:
    t = _ir_get(ir, "SessionTime")
    return float(t) if t is not None else 0.0


def _replay_frame(ir: Any) -> Optional[int]:
    f = _ir_get(ir, "ReplayFrameNum")
    return int(f) if f is not None else None


def _focus_val(ir: Any, key: str, focus_idx: int) -> Any:
    """Get value for focus car from CarIdx* array."""
    if not ir:
        return None
    arr = _ir_get(ir, key)
    if arr is None or not isinstance(arr, (list, tuple)):
        return None
    if 0 <= focus_idx < len(arr):
        return arr[focus_idx]
    return None


def _current_lap(ir: Any, focus_idx: int) -> int:
    """Lap in progress (1-based for display). CarIdxLapCompleted is 0-based laps done."""
    completed = _focus_val(ir, "CarIdxLapCompleted", focus_idx)
    if completed is None or completed < 0:
        return 1
    return int(completed) + 1


def _position_by_car_idx(ir: Any) -> Dict[int, int]:
    """Map car_idx -> race position (1-based)."""
    pos_arr = _ir_get(ir, "CarIdxPosition")
    if not isinstance(pos_arr, (list, tuple)):
        return {}
    return {i: int(pos_arr[i]) for i in range(len(pos_arr)) if pos_arr[i] is not None and int(pos_arr[i]) > 0}


def _car_idx_at_position(ir: Any, position: int) -> Optional[int]:
    """Return car_idx that has the given race position (1-based)."""
    for idx, pos in _position_by_car_idx(ir).items():
        if pos == position:
            return idx
    return None


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
        current = _focus_val(ir, "CarIdxLapCompleted", focus_idx)
        return (None, current if current is not None else prev_lap_completed)
    current = _focus_val(ir, "CarIdxLapCompleted", focus_idx)
    if current is None:
        return (None, prev_lap_completed)
    prev = -1 if prev_lap_completed is None else prev_lap_completed
    if int(current) > prev and prev >= 0:
        lap = int(current)  # completed lap number (1-based for display)
        session_time = _session_time(ir)
        lap_time = _focus_val(ir, "CarIdxLastLapTime", focus_idx)
        position = _focus_val(ir, "CarIdxPosition", focus_idx)
        class_pos = _focus_val(ir, "CarIdxClassPosition", focus_idx)
        ev = base_event(LAP_COMPLETE, session_time, lap, replay_frame=_replay_frame(ir))
        if lap_time is not None and float(lap_time) > 0:
            ev["lap_time"] = float(lap_time)
        if position is not None:
            ev["position"] = int(position)
        if class_pos is not None:
            ev["class_position"] = int(class_pos)
        return (ev, int(current))
    return (None, int(current))


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
    pos_arr = _ir_get(ir, "CarIdxPosition")
    if not isinstance(pos_arr, (list, tuple)) or focus_idx >= len(pos_arr):
        return (events, prev_position or 0)
    new_pos = int(pos_arr[focus_idx]) if pos_arr[focus_idx] is not None else None
    if new_pos is None or new_pos <= 0:
        return (events, prev_position or 0)
    session_time = _session_time(ir)
    prev = prev_position
    if prev is not None and prev > 0 and new_pos != prev:
        if new_pos < prev and PASS in (event_types_enabled or [PASS]):
            if event_types_enabled is None or PASS in event_types_enabled:
                passed_pos = new_pos
                other_idx = _car_idx_at_position(ir, prev)
                num, name = car_number_and_name(get_driver_by_car_idx(driver_info, other_idx)) if other_idx is not None else ("", "")
                ev = base_event(PASS, session_time, current_lap, replay_frame=_replay_frame(ir))
                ev["passed_car_number"] = num or "?"
                ev["new_position"] = new_pos
                if other_idx is not None:
                    ev["passed_car_idx"] = other_idx
                if name:
                    ev["passed_driver_name"] = name
                ev["old_position"] = prev
                class_pos = _focus_val(ir, "CarIdxClassPosition", focus_idx)
                if class_pos is not None:
                    ev["class_position"] = int(class_pos)
                events.append(ev)
        if new_pos > prev and GOT_PASSED in (event_types_enabled or [GOT_PASSED]):
            if event_types_enabled is None or GOT_PASSED in event_types_enabled:
                other_idx = _car_idx_at_position(ir, prev)
                num, name = car_number_and_name(get_driver_by_car_idx(driver_info, other_idx)) if other_idx is not None else ("", "")
                ev = base_event(GOT_PASSED, session_time, current_lap, replay_frame=_replay_frame(ir))
                ev["by_car_number"] = num or "?"
                ev["new_position"] = new_pos
                if other_idx is not None:
                    ev["by_car_idx"] = other_idx
                if name:
                    ev["by_driver_name"] = name
                ev["old_position"] = prev
                class_pos = _focus_val(ir, "CarIdxClassPosition", focus_idx)
                if class_pos is not None:
                    ev["class_position"] = int(class_pos)
                events.append(ev)
    return (events, new_pos)


def check_pit(
    ir: Any,
    focus_idx: int,
    prev_on_pit_road: Optional[bool],
    current_lap: int,
    event_types_enabled: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Detect pit_entry (false->true) and pit_exit (true->false).
    Returns (list of events, updated prev_on_pit_road).
    """
    events: List[Dict[str, Any]] = []
    on_now = _focus_val(ir, "CarIdxOnPitRoad", focus_idx)
    if on_now is None:
        return (events, prev_on_pit_road if prev_on_pit_road is not None else False)
    on_now = bool(on_now)
    prev = prev_on_pit_road
    session_time = _session_time(ir)
    if prev is not None:
        if not prev and on_now and (event_types_enabled is None or PIT_ENTRY in event_types_enabled):
            ev = base_event(PIT_ENTRY, session_time, current_lap, replay_frame=_replay_frame(ir))
            pos = _focus_val(ir, "CarIdxPosition", focus_idx)
            if pos is not None:
                ev["position"] = int(pos)
            lap_pct = _focus_val(ir, "CarIdxLapDistPct", focus_idx)
            if lap_pct is not None and 0 <= float(lap_pct) <= 1:
                ev["lap_pct"] = float(lap_pct)
            events.append(ev)
        if prev and not on_now and (event_types_enabled is None or PIT_EXIT in event_types_enabled):
            ev = base_event(PIT_EXIT, session_time, current_lap, replay_frame=_replay_frame(ir))
            pos = _focus_val(ir, "CarIdxPosition", focus_idx)
            if pos is not None:
                ev["position"] = int(pos)
            lap_pct = _focus_val(ir, "CarIdxLapDistPct", focus_idx)
            if lap_pct is not None and 0 <= float(lap_pct) <= 1:
                ev["lap_pct"] = float(lap_pct)
            events.append(ev)
    return (events, on_now)


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
        status = _ir_get(ir, "PlayerCarPitSvStatus")
        return (None, status if status is not None else prev_pit_sv_status)
    if focus_idx != player_car_idx:
        return (None, prev_pit_sv_status)
    status = _ir_get(ir, "PlayerCarPitSvStatus")
    if status is None:
        return (None, prev_pit_sv_status)
    status = int(status)
    if status == 2 and (prev_pit_sv_status is None or prev_pit_sv_status != 2):
        session_time = _session_time(ir)
        ev = base_event(PIT_STOP_COMPLETE, session_time, current_lap, replay_frame=_replay_frame(ir))
        if pit_entry_session_time is not None:
            ev["pit_duration"] = round(session_time - pit_entry_session_time, 2)
        return (ev, status)
    return (None, status)


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
        cnt = _ir_get(ir, "PlayerCarMyIncidentCount") if focus_idx == player_car_idx else None
        return (None, cnt if cnt is not None else prev_incident_count)
    if focus_idx != player_car_idx:
        return (None, prev_incident_count)
    count = _ir_get(ir, "PlayerCarMyIncidentCount")
    if count is None:
        return (None, prev_incident_count)
    count = int(count)
    prev = prev_incident_count if prev_incident_count is not None else 0
    if count > prev:
        session_time = _session_time(ir)
        ev = base_event(INCIDENT, session_time, current_lap, replay_frame=_replay_frame(ir))
        ev["incident_count"] = count
        flags = _ir_get(ir, "PlayerIncidents")
        if flags is not None:
            ev["flags"] = int(flags)
        surf = _focus_val(ir, "CarIdxTrackSurface", focus_idx)
        if surf is not None:
            ev["track_surface"] = int(surf)
        ev["kind"] = "unknown"
        return (ev, count)
    return (None, count)


def check_close_battle(
    ir: Any,
    focus_idx: int,
    player_car_idx: Optional[int],
    driver_info: Any,
    current_lap: int,
    battle_gap_s: float,
    battle_gap_m: float = 80.0,
    event_types_enabled: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    If focus car has small gap ahead and/or behind, emit close_battle.
    When focus is player use CarDistAhead/CarDistBehind (threshold battle_gap_m); else CarIdxF2Time (battle_gap_s).
    """
    if event_types_enabled is not None and CLOSE_BATTLE not in event_types_enabled:
        return None
    session_time = _session_time(ir)
    ev = base_event(CLOSE_BATTLE, session_time, current_lap, replay_frame=_replay_frame(ir))
    if focus_idx == player_car_idx:
        ahead = _ir_get(ir, "CarDistAhead")
        behind = _ir_get(ir, "CarDistBehind")
        if ahead is not None and float(ahead) >= 0:
            ev["gap_ahead_m"] = round(float(ahead), 2)
        if behind is not None and float(behind) >= 0:
            ev["gap_behind_m"] = round(float(behind), 2)
        if ahead is not None and float(ahead) < 1000:
            ev["gap_ahead_s"] = round(float(ahead) / 60.0, 2)
        if behind is not None and float(behind) < 1000:
            ev["gap_behind_s"] = round(float(behind) / 60.0, 2)
        if (ahead is None or float(ahead) > battle_gap_m) and (behind is None or float(behind) > battle_gap_m):
            return None
    else:
        f2 = _focus_val(ir, "CarIdxF2Time", focus_idx)
        if f2 is None or float(f2) < 0 or float(f2) > battle_gap_s:
            return None
        ev["gap_ahead_s"] = round(float(f2), 2)
        pos_by_idx = _position_by_car_idx(ir)
        my_pos = pos_by_idx.get(focus_idx)
        if my_pos is not None:
            ahead_idx = _car_idx_at_position(ir, my_pos - 1)
            behind_idx = _car_idx_at_position(ir, my_pos + 1)
            if ahead_idx is not None:
                num, _ = car_number_and_name(get_driver_by_car_idx(driver_info, ahead_idx))
                ev["car_ahead_number"] = num
                ev["car_ahead_idx"] = ahead_idx
            if behind_idx is not None:
                num, _ = car_number_and_name(get_driver_by_car_idx(driver_info, behind_idx))
                ev["car_behind_number"] = num
                ev["car_behind_idx"] = behind_idx
    if len(ev) <= 4:
        return None
    return ev


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
    _, prev_name = car_number_and_name(prev_driver) if prev_driver else ("", "")
    if prev_name != curr_name and (curr_name or prev_name):
        ev = base_event(DRIVER_CHANGE, session_time, current_lap)
        ev["current_driver_name"] = curr_name
        ev["previous_driver_name"] = prev_name
        ev["direction"] = "in"
        return ev
    return None

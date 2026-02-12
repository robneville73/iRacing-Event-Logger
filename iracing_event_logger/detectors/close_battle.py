"""Detect close battle (small gap ahead/behind)."""

from typing import Any, Dict, List, Optional

from ..events import CLOSE_BATTLE, base_event
from ..sdk_wrapper import car_number_and_name, get_driver_by_car_idx
from .common import (
    car_idx_at_position,
    focus_val,
    ir_get,
    position_by_car_idx,
    replay_frame,
    session_time,
)


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
    When focus is player use CarDistAhead/CarDistBehind (threshold battle_gap_m);
    else CarIdxF2Time (battle_gap_s).
    """
    if event_types_enabled is not None and CLOSE_BATTLE not in event_types_enabled:
        return None
    session_time_val = session_time(ir)
    ev = base_event(
        CLOSE_BATTLE, session_time_val, current_lap, replay_frame=replay_frame(ir)
    )
    if focus_idx == player_car_idx:
        ahead = ir_get(ir, "CarDistAhead")
        behind = ir_get(ir, "CarDistBehind")
        if ahead is not None and float(ahead) >= 0:
            ev["gap_ahead_m"] = round(float(ahead), 2)
        if behind is not None and float(behind) >= 0:
            ev["gap_behind_m"] = round(float(behind), 2)
        if ahead is not None and float(ahead) < 1000:
            ev["gap_ahead_s"] = round(float(ahead) / 60.0, 2)
        if behind is not None and float(behind) < 1000:
            ev["gap_behind_s"] = round(float(behind) / 60.0, 2)
        if (ahead is None or float(ahead) > battle_gap_m) and (
            behind is None or float(behind) > battle_gap_m
        ):
            return None
    else:
        f2 = focus_val(ir, "CarIdxF2Time", focus_idx)
        if f2 is None or float(f2) < 0 or float(f2) > battle_gap_s:
            return None
        ev["gap_ahead_s"] = round(float(f2), 2)
        pos_by_idx = position_by_car_idx(ir)
        my_pos = pos_by_idx.get(focus_idx)
        if my_pos is not None:
            ahead_idx = car_idx_at_position(ir, my_pos - 1)
            behind_idx = car_idx_at_position(ir, my_pos + 1)
            if ahead_idx is not None:
                num, _ = car_number_and_name(
                    get_driver_by_car_idx(driver_info, ahead_idx)
                )
                ev["car_ahead_number"] = num
                ev["car_ahead_idx"] = ahead_idx
            if behind_idx is not None:
                num, _ = car_number_and_name(
                    get_driver_by_car_idx(driver_info, behind_idx)
                )
                ev["car_behind_number"] = num
                ev["car_behind_idx"] = behind_idx
    if len(ev) <= 4:
        return None
    return ev

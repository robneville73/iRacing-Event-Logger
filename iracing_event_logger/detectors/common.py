"""Shared helpers for reading from the iRacing SDK (no .get method)."""

from typing import Any, Dict, Optional


def ir_get(ir: Any, key: str, default: Any = None) -> Any:
    """Safe read from SDK."""
    if not ir:
        return default
    try:
        v = ir[key]
        return v if v is not None else default
    except (KeyError, TypeError, IndexError):
        return default


def session_time(ir: Any) -> float:
    """Current session time from telemetry."""
    t = ir_get(ir, "SessionTime")
    return float(t) if t is not None else 0.0


def replay_frame(ir: Any) -> Optional[int]:
    """Replay frame number if available."""
    f = ir_get(ir, "ReplayFrameNum")
    return int(f) if f is not None else None


def focus_val(ir: Any, key: str, focus_idx: int) -> Any:
    """Get value for focus car from CarIdx* array."""
    if not ir:
        return None
    arr = ir_get(ir, key)
    if arr is None or not isinstance(arr, (list, tuple)):
        return None
    if 0 <= focus_idx < len(arr):
        return arr[focus_idx]
    return None


def current_lap(ir: Any, focus_idx: int) -> int:
    """Lap in progress (1-based for display). CarIdxLapCompleted is 0-based laps done."""
    completed = focus_val(ir, "CarIdxLapCompleted", focus_idx)
    if completed is None or completed < 0:
        return 1
    return int(completed) + 1


def position_by_car_idx(ir: Any) -> Dict[int, int]:
    """Map car_idx -> race position (1-based)."""
    pos_arr = ir_get(ir, "CarIdxPosition")
    if not isinstance(pos_arr, (list, tuple)):
        return {}
    return {
        i: int(pos_arr[i])
        for i in range(len(pos_arr))
        if pos_arr[i] is not None and int(pos_arr[i]) > 0
    }


def car_idx_at_position(ir: Any, position: int) -> Optional[int]:
    """Return car_idx that has the given race position (1-based)."""
    for idx, pos in position_by_car_idx(ir).items():
        if pos == position:
            return idx
    return None

"""Main telemetry loop: poll SDK, run detectors, write events, flush on lap completion."""

import logging
import time
from typing import Any, Dict, Optional

from .config import (
    get_battle_gap_s,
    get_event_types_enabled,
    get_focus_car,
    get_focus_driver,
    get_start_telemetry,
)
from .detectors import (
    check_close_battle,
    check_driver_change,
    check_incident,
    check_lap_complete,
    check_pit,
    check_pit_stop_complete,
    check_position_changes,
    current_lap,
)
from .log_writer import LogWriter
from .sdk_wrapper import (
    IRacingSDK,
    FocusCar,
    resolve_focus_car,
)

logger = logging.getLogger(__name__)

# Poll interval ~60 Hz
TICK_SLEEP_S = 0.016
# Throttle close_battle to at most once per this many seconds
CLOSE_BATTLE_THROTTLE_S = 2.0


def run(config: Dict[str, Any], writer: Optional[LogWriter] = None) -> None:
    """
    Connect to iRacing, resolve focus car, then run the telemetry loop until disconnect.
    Events are written to the provided LogWriter; if None, a default is created from config.
    """
    from .config import get_log_file

    sdk = IRacingSDK()
    if not sdk.startup():
        logger.error("Could not connect to iRacing. Is the sim running?")
        return

    focus_driver = get_focus_driver(config)
    focus_car = get_focus_car(config)
    driver_info = sdk["DriverInfo"]
    focus = resolve_focus_car(driver_info, focus_driver, focus_car)
    if not focus:
        logger.warning("No focus driver/car specified or not found in session. Logging all cars disabled.")
        sdk.shutdown()
        return

    if get_start_telemetry(config):
        sdk.telem_start()
        logger.info("Telemetry recording started.")

    session_id = str(sdk["SessionUniqueID"] or "")
    track = ""
    try:
        weekend = sdk["WeekendInfo"]
        if isinstance(weekend, dict) and "TrackDisplayName" in weekend:
            track = str(weekend["TrackDisplayName"] or "")
    except (TypeError, KeyError):
        pass

    if writer is None:
        writer = LogWriter(
            get_log_file(config),
            session_id=session_id,
            focus_car=focus,
            track=track,
            start_time_utc="",
        )
    else:
        writer.set_session(session_id=session_id, focus_car=focus, track=track)

    focus_idx = focus.car_idx
    try:
        player_car_idx = sdk["PlayerCarIdx"]
    except (TypeError, KeyError):
        player_car_idx = None
    if player_car_idx is not None:
        player_car_idx = int(player_car_idx)
    battle_gap_s = get_battle_gap_s(config)
    event_types = get_event_types_enabled(config)

    state: Dict[str, Any] = {
        "prev_position": None,
        "prev_on_pit_road": None,
        "prev_lap_completed": None,
        "prev_incident_count": None,
        "prev_driver_info": None,
        "prev_pit_sv_status": None,
        "pit_entry_session_time": None,
        "last_close_battle_time": None,
    }

    try:
        while sdk.is_connected:
            _tick(sdk, focus, focus_idx, player_car_idx, config, writer, state, battle_gap_s, event_types)
            time.sleep(TICK_SLEEP_S)
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    finally:
        writer.flush()
        sdk.shutdown()


def _tick(
    sdk: IRacingSDK,
    focus: FocusCar,
    focus_idx: int,
    player_car_idx: Optional[int],
    config: Dict[str, Any],
    writer: LogWriter,
    state: Dict[str, Any],
    battle_gap_s: float,
    event_types: Optional[list],
) -> None:
    """One iteration: read telemetry, run detectors, append events, flush on lap complete."""
    ir = sdk._ir
    if not ir:
        return
    try:
        session_time = float(ir["SessionTime"] or 0)
    except (TypeError, KeyError):
        session_time = 0.0

    driver_info = sdk["DriverInfo"]
    current_lap_val = current_lap(ir, focus_idx)

    # Lap complete
    ev_lap, state["prev_lap_completed"] = check_lap_complete(
        ir, focus_idx, state["prev_lap_completed"], event_types
    )
    if ev_lap:
        writer.add_event(ev_lap["lap"], ev_lap)
        writer.flush()

    # Position changes (pass / got_passed)
    pos_events, state["prev_position"] = check_position_changes(
        ir, focus_idx, state["prev_position"], driver_info, current_lap_val, event_types
    )
    for e in pos_events:
        writer.add_event(current_lap_val, e)

    # Pit entry/exit
    pit_events, state["prev_on_pit_road"] = check_pit(
        ir, focus_idx, state["prev_on_pit_road"], current_lap_val, event_types
    )
    for e in pit_events:
        writer.add_event(current_lap_val, e)
        if e.get("type") == "pit_entry":
            state["pit_entry_session_time"] = e.get("session_time")
        if e.get("type") == "pit_exit":
            state["pit_entry_session_time"] = None

    # Pit stop complete (focus = player only)
    pit_complete_ev, state["prev_pit_sv_status"] = check_pit_stop_complete(
        ir, focus_idx, player_car_idx, state["prev_pit_sv_status"],
        state.get("pit_entry_session_time"), current_lap_val, event_types
    )
    if pit_complete_ev:
        writer.add_event(current_lap_val, pit_complete_ev)

    # Incident (focus = player only)
    inc_ev, state["prev_incident_count"] = check_incident(
        ir, focus_idx, player_car_idx, state["prev_incident_count"], current_lap_val, event_types
    )
    if inc_ev:
        writer.add_event(current_lap_val, inc_ev)

    # Close battle (throttled)
    if state["last_close_battle_time"] is None or (session_time - state["last_close_battle_time"]) >= CLOSE_BATTLE_THROTTLE_S:
        battle_ev = check_close_battle(
            ir, focus_idx, player_car_idx, driver_info, current_lap_val, battle_gap_s, 80.0, event_types
        )
        if battle_ev:
            writer.add_event(current_lap_val, battle_ev)
            state["last_close_battle_time"] = session_time

    # Driver change (compare to previous DriverInfo)
    dc_ev = check_driver_change(
        driver_info, state["prev_driver_info"], focus_idx, session_time, current_lap_val, event_types
    )
    if dc_ev:
        writer.add_event(current_lap_val, dc_ev)
    state["prev_driver_info"] = driver_info

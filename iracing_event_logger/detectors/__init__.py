"""Event detection: compare current telemetry/session to previous state and emit events."""

from .common import current_lap
from .close_battle import check_close_battle
from .driver_change import check_driver_change
from .incident import check_incident
from .lap_complete import check_lap_complete
from .pit import check_pit
from .pit_stop_complete import check_pit_stop_complete
from .position_changes import check_position_changes

__all__ = [
    "check_close_battle",
    "check_driver_change",
    "check_incident",
    "check_lap_complete",
    "check_pit",
    "check_pit_stop_complete",
    "check_position_changes",
    "current_lap",
]

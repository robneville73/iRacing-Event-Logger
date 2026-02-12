"""SDK connection and session/telemetry access with focus car resolution."""

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import irsdk
except ImportError:
    irsdk = None  # type: ignore


class FocusCar:
    """Resolved focus car: car_idx and identifiers from session."""

    def __init__(
        self,
        car_idx: int,
        car_number: str,
        driver_name: str = "",
    ) -> None:
        self.car_idx = car_idx
        self.car_number = str(car_number)
        self.driver_name = driver_name or ""

    def to_session_dict(self) -> Dict[str, Any]:
        """For inclusion in log session header."""
        return {
            "car_idx": self.car_idx,
            "car_number": self.car_number,
            "driver_name": self.driver_name,
        }


def resolve_focus_car(
    driver_info: Any,
    focus_driver: Optional[str] = None,
    focus_car: Optional[str] = None,
) -> Optional[FocusCar]:
    """
    Resolve focus driver or car number to FocusCar (car_idx + identifiers).

    driver_info: Parsed DriverInfo from session YAML (e.g. ir['DriverInfo']).
    focus_driver: Driver name or abbrev to match (UserName / AbbrevName).
    focus_car: Car number to match (e.g. "5" or "05").
    Returns FocusCar or None if not found or no focus specified.
    """
    if not focus_driver and not focus_car:
        return None
    if not driver_info:
        return None

    drivers: List[Dict[str, Any]] = []
    if isinstance(driver_info, dict) and "Drivers" in driver_info:
        drivers = driver_info["Drivers"] or []
    elif isinstance(driver_info, list):
        drivers = driver_info

    for d in drivers:
        if not isinstance(d, dict):
            continue
        car_idx = d.get("CarIdx")
        car_number = d.get("CarNumber") or d.get("CarNumberRaw") or ""
        user_name = (d.get("UserName") or "").strip()
        abbrev = (d.get("AbbrevName") or "").strip()

        if focus_car is not None and str(car_number).strip() == str(focus_car).strip():
            return FocusCar(
                car_idx=int(car_idx) if car_idx is not None else -1,
                car_number=str(car_number).strip(),
                driver_name=user_name or abbrev,
            )
        if focus_driver and (user_name == focus_driver or abbrev == focus_driver):
            return FocusCar(
                car_idx=int(car_idx) if car_idx is not None else -1,
                car_number=str(car_number).strip(),
                driver_name=user_name or abbrev,
            )

    return None


def get_driver_by_car_idx(driver_info: Any, car_idx: int) -> Optional[Dict[str, Any]]:
    """Return driver dict for the given car index, or None."""
    if not driver_info:
        return None
    drivers: List[Dict[str, Any]] = []
    if isinstance(driver_info, dict) and "Drivers" in driver_info:
        drivers = driver_info["Drivers"] or []
    elif isinstance(driver_info, list):
        drivers = driver_info
    for d in drivers:
        if isinstance(d, dict) and d.get("CarIdx") == car_idx:
            return d
    return None


def car_number_and_name(driver: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    """(car_number, driver_name) from a driver dict."""
    if not driver:
        return ("", "")
    num = (driver.get("CarNumber") or driver.get("CarNumberRaw") or "")
    name = (driver.get("UserName") or driver.get("AbbrevName") or "").strip()
    return (str(num).strip(), name)


class IRacingSDK:
    """
    Thin wrapper around pyirsdk: connect, read telemetry/session, optional broadcast.
    """

    def __init__(self) -> None:
        self._ir: Any = None
        if irsdk:
            self._ir = irsdk.IRSDK()

    @property
    def is_connected(self) -> bool:
        return bool(self._ir and self._ir.is_connected)

    def startup(self) -> bool:
        """Connect to iRacing; returns True if connected."""
        if not irsdk:
            logger.error("pyirsdk not installed")
            return False
        if self._ir.startup():
            logger.info("Connected to iRacing SDK")
            return True
        return False

    def shutdown(self) -> None:
        if self._ir:
            self._ir.shutdown()
            self._ir = None
        logger.info("Disconnected from iRacing SDK")

    def __getitem__(self, key: str) -> Any:
        """Read telemetry or session key (e.g. 'SessionTime', 'CarIdxPosition', 'DriverInfo')."""
        if not self._ir:
            return None
        try:
            return self._ir[key]
        except (KeyError, TypeError):
            return None

    def telem_start(self) -> None:
        """Start telemetry recording (broadcast)."""
        if not irsdk or not self._ir or not hasattr(self._ir, "telem_command"):
            return
        self._ir.telem_command(irsdk.TelemCommandMode.start)

"""Lap-organized JSON log writer. Flushes full file on lap completion or shutdown."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .events import base_event
from .sdk_wrapper import FocusCar

logger = logging.getLogger(__name__)


class LogWriter:
    """
    Writes events into a lap-organized JSON log.
    Session header is set once; events are appended to laps by lap number.
    Full file is written on flush (lap completion or shutdown).
    """

    def __init__(
        self,
        log_path: str,
        session_id: str = "",
        focus_car: Optional[FocusCar] = None,
        track: str = "",
        start_time_utc: str = "",
    ) -> None:
        self.log_path = Path(log_path)
        self._session: Dict[str, Any] = {
            "session_id": session_id,
            "focus_car": focus_car.to_session_dict() if focus_car else {},
            "track": track,
            "start_time_utc": start_time_utc,
        }
        self._laps: Dict[str, List[Dict[str, Any]]] = {}
        self._dirty = False

    def set_session(
        self,
        session_id: str = "",
        focus_car: Optional[FocusCar] = None,
        track: str = "",
        start_time_utc: str = "",
    ) -> None:
        """Update session header (e.g. after first connect)."""
        if session_id:
            self._session["session_id"] = session_id
        if focus_car:
            self._session["focus_car"] = focus_car.to_session_dict()
        if track:
            self._session["track"] = track
        if start_time_utc:
            self._session["start_time_utc"] = start_time_utc
        self._dirty = True

    def add_event(self, lap: int, event: Dict[str, Any]) -> None:
        """Append an event to the given lap (1-based)."""
        key = str(lap)
        if key not in self._laps:
            self._laps[key] = []
        self._laps[key].append(event)
        self._dirty = True

    def flush(self) -> None:
        """Write full log to disk. Call on lap completion or shutdown."""
        if not self._dirty:
            return
        payload = {
            "session": self._session,
            "laps": self._laps,
        }
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            self._dirty = False
            logger.debug("Flushed log to %s", self.log_path)
        except OSError as e:
            logger.error("Failed to write log to %s: %s", self.log_path, e)

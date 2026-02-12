"""Entry point: parse config/CLI, wire components, run main loop."""

import argparse
import logging
import sys
import traceback
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# When running as frozen exe, log next to the exe (guaranteed writable)
def _get_app_log_path() -> Optional[Path]:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "app.log"
    return None


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="iRacing Event Logger: stream session/telemetry and log interesting events by lap."
    )
    p.add_argument(
        "--focus-driver",
        metavar="NAME",
        help="Focus on driver by name (UserName or AbbrevName).",
    )
    p.add_argument(
        "--focus-car",
        metavar="NUMBER",
        help="Focus on car by number (e.g. 5 or 05).",
    )
    p.add_argument(
        "--config",
        metavar="FILE",
        type=Path,
        help="Config file (YAML or JSON). Overrides default search.",
    )
    p.add_argument(
        "--log-file",
        metavar="PATH",
        help="Output JSON log file path.",
    )
    p.add_argument(
        "--battle-gap-s",
        type=float,
        metavar="SEC",
        help="Time gap (seconds) below which to emit close_battle (spectating). Default from config.",
    )
    p.add_argument(
        "--start-telemetry",
        action="store_true",
        help="Start iRacing telemetry recording on connect.",
    )
    p.add_argument(
        "--no-start-telemetry",
        action="store_true",
        help="Do not start telemetry even if config says so.",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose (DEBUG) logging.",
    )
    return p.parse_args()


def main() -> None:
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=log_datefmt,
    )

    # Add file handler first (when frozen) so we capture everything
    app_log = _get_app_log_path()
    if app_log:
        try:
            file_handler = logging.FileHandler(app_log, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(log_format, datefmt=log_datefmt))
            logging.getLogger().addHandler(file_handler)
            logger.info("Logging to %s", app_log)
        except OSError as e:
            logging.getLogger().warning("Could not create app log %s: %s", app_log, e)

    args = _parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        if app_log and logging.getLogger().handlers:
            for h in logging.getLogger().handlers:
                if isinstance(h, logging.FileHandler):
                    h.setLevel(logging.DEBUG)

    from iracing_event_logger.config import load_config
    from iracing_event_logger.loop import run

    config = load_config(args.config)
    if args.focus_driver is not None:
        config["focus_driver"] = args.focus_driver
    if args.focus_car is not None:
        config["focus_car"] = args.focus_car
    if args.log_file is not None:
        config["log_file"] = args.log_file
    if args.battle_gap_s is not None:
        config["battle_gap_s"] = args.battle_gap_s
    if args.start_telemetry:
        config["start_telemetry"] = True
    if args.no_start_telemetry:
        config["start_telemetry"] = False

    if not config.get("focus_driver") and not config.get("focus_car"):
        logger.error("Specify --focus-driver or --focus-car (or set in config).")
        if getattr(sys, "frozen", False):
            input("Press Enter to exit...")
        sys.exit(1)

    success = run(config)
    if not success and getattr(sys, "frozen", False):
        input("Press Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        app_log = _get_app_log_path()
        err_msg = traceback.format_exc()
        if app_log:
            try:
                with open(app_log, "a", encoding="utf-8") as f:
                    f.write(err_msg)
            except OSError:
                pass
        print(err_msg)
        if getattr(sys, "frozen", False):
            input("Press Enter to exit...")
        raise

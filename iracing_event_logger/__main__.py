"""Entry point: parse config/CLI, wire components, run main loop."""

import argparse
import logging
import sys
from pathlib import Path

from .config import load_config, get_log_file, get_start_telemetry
from .loop import run

logger = logging.getLogger(__name__)


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
    args = _parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

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
        sys.exit(1)

    run(config)


if __name__ == "__main__":
    main()

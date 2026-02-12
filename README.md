# iRacing Event Logger

Stream iRacing session and telemetry data and produce a **lap-organized JSON log** of "interesting events" for a focus driver or car. Downstream applications can consume this log for camera control, automatic video editing, or analytics.

## Requirements

- Python 3.7+
- [iRacing](https://www.iracing.com/) with the sim running (or at least the SDK available)
- Windows (pyirsdk uses Windows shared memory and APIs)

## Installation

1. Clone the repository and create a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # or: source .venv/bin/activate  # Linux/macOS
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the logger (see Usage below).

## Usage

You must specify a **focus** so the log stays manageable: either a driver name or a car number.

**Focus by car number:**

```bash
python -m iracing_event_logger --focus-car 5
```

**Focus by driver name (UserName or AbbrevName from the session):**

```bash
python -m iracing_event_logger --focus-driver "John Doe"
```

**Optional arguments:**

- `--config FILE` – Use this config file (YAML or JSON) instead of the default search paths.
- `--log-file PATH` – Output JSON log file (default: `event_log.json`).
- `--battle-gap-s SEC` – Time gap in seconds below which to emit `close_battle` when spectating (default: 1.5).
- `--start-telemetry` – Start iRacing telemetry recording on connect.
- `--no-start-telemetry` – Do not start telemetry even if config says so.
- `-v` / `--verbose` – Debug logging.

Start iRacing (or join a session), then run the logger. It will connect to the SDK, resolve the focus car, and write events to the log file. The file is flushed on each lap completion and on exit.

## Configuration file

Config is optional. Search order:

1. `config.yaml` or `config.json` in the current directory
2. `~/.config/iracing-event-logger/config.yaml` or `config.json`

Example `config.yaml`:

```yaml
focus_car: "5"
# or: focus_driver: "Your Name"
log_file: "event_log.json"
battle_gap_s: 1.5
start_telemetry: false
# event_types: [ "lap_complete", "pass", "got_passed", "pit_entry", "pit_exit", "close_battle", "incident" ]
```

CLI options override config. Environment overrides: `IRACING_LOG_LOG_FILE`, `IRACING_LOG_FOCUS_CAR`, `IRACING_LOG_FOCUS_DRIVER`, `IRACING_LOG_BATTLE_GAP_S`, `IRACING_LOG_START_TELEMETRY`.

## Log format

The output is a single JSON file with:

- **session** – `session_id`, `focus_car` (car_number, car_idx, driver_name), `track`, `start_time_utc`.
- **laps** – Object mapping lap number (string) to an array of event objects.

Each event has at least:

- `type` – Event type (e.g. `lap_complete`, `pass`, `pit_entry`, `close_battle`, `incident`).
- `session_time` – Seconds since session start (for replay/cuts).
- `lap` – Lap number (1-based).

See the source (`events.py`, `detectors.py`, `log_writer.py`) and docstrings for the full schema of each event type.

## Event types

| Type | Description |
|------|-------------|
| `lap_complete` | Focus car completed a lap (lap time, position). |
| `pass` | Focus car overtook another car. |
| `got_passed` | Focus car was overtaken. |
| `pit_entry` | Focus car entered pit lane. |
| `pit_exit` | Focus car left pits. |
| `pit_stop_complete` | Pit service finished (when focus is the player). |
| `incident` | Spin, contact, or off-track (when focus is the player). |
| `close_battle` | Small gap ahead or behind (for camera/battle highlight). |
| `driver_change` | Endurance: driver in/out (when DriverInfo changes). |

## Building the installer

To create a Windows exe and installer (no Python required for end users):

**Prerequisites**

- Python 3.7+
- [Inno Setup 6](https://jrsoftware.org/isinfo.php)

**Steps**

1. Create and activate a virtual environment, then install build dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-build.txt
   ```

2. Build the exe with PyInstaller:

   ```bash
   pyinstaller event_logger.spec
   ```

   This produces `dist\iRacingEventLogger.exe`.

3. Build the installer with Inno Setup:

   ```bash
   iscc installer.iss
   ```

   This produces `Output\iRacingEventLogger-Setup.exe`.

The installer prompts for focus (car number or driver name), log file path, battle gap, and whether to start telemetry. It writes `config.yaml` to `%USERPROFILE%\.config\iracing-event-logger\`.

**Troubleshooting:** When the installed exe runs, it writes an `app.log` file to the same folder as the exe (e.g. `%LOCALAPPDATA%\iRacing Event Logger\app.log`). On error, the console window stays open until you press Enter so you can read the message.

## Development

- Follow PEP 8 and the project [coding_standards.md](coding_standards.md).
- Tests: `pytest` (add tests under `tests/` with mocked or canned SDK data).
- Type hints are used for public APIs and event payloads.

## License

See repository license file.

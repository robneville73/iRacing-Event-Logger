This program should be written in Python and follow PEP-8 coding standards. It should install all dependencies in a virtual environment.

## Project structure

- Use a single top-level package `iracing_event_logger/` with modules for SDK wrapper, event detection, log writer, and CLI.
- Keep `main` or `__main__` thin: parse config/CLI, wire components, run loop.

## Dependencies

- Pin versions in `requirements.txt` (e.g. `pyirsdk`, `PyYAML`). Install only in a virtual environment; document venv creation in README.

## Configuration

- Use a single config module; support loading from YAML or JSON and override with environment variables or CLI where appropriate.

## Logging

- Use the standard `logging` module; no `print` for operational messages. Log level configurable via config or env.

## Testing

- Prefer pytest; unit tests for event detection logic with mocked or canned SDK data (e.g. from a dumped session YAML + telemetry snapshot).

## Type hints

- Use type hints for public functions and event payloads to clarify the contract for downstream consumers and avoid misuse of the JSON log.

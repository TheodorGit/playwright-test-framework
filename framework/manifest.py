"""
The run's record: what ran and how each test ended, written as it happens.

Each test owns one file, rewritten after every phase, so a run that is
killed still leaves an honest record and pytest-xdist workers never write
over each other.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from framework.reporting.recorder import safe_name

RUN_FILE = "run.json"
SELECTION_FILE = "selection.json"
TESTS_DIR = "tests"
IN_FLIGHT = "the run ended while this test was still executing"


def start_run(directory, run_id: str, environment: str = None,
              label: str = None) -> Path:
    """Writes the run's header, before the first test."""
    path = Path(directory) / RUN_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "run_id": run_id,
        "environment": environment,
        "label": label or None,
        "started": datetime.now(UTC).isoformat(timespec="seconds"),
        "finished": None,
        "duration": 0.0,
    }, indent=2), encoding="utf-8")
    return path


def read_run(directory) -> dict:
    path = Path(directory) / RUN_FILE
    if not path.exists():
        raise FileNotFoundError(f"{path} not found: nothing authoritative to "
                                f"report on")
    return json.loads(path.read_text(encoding="utf-8"))


def record_selection(directory, collected: int, selected: int,
                     expression: str = "") -> Path:
    """What the run was asked to run, written while collection still knows.

    Every pytest-xdist worker collects the same suite and writes the same
    numbers, so the replace is what keeps a reader from meeting half a file.
    """
    path = Path(directory) / SELECTION_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(f".{os.getpid()}.json")
    partial.write_text(json.dumps({
        "collected": collected,
        "selected": selected,
        "deselected": collected - selected,
        "expression": expression or "",
    }, indent=2), encoding="utf-8")
    os.replace(partial, path)
    return path


def read_selection(directory) -> dict:
    """The run's selection, or nothing at all for a run that recorded none."""
    path = Path(directory) / SELECTION_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def finish_run(directory) -> Path:
    header = read_run(directory)
    now = datetime.now(UTC)
    header["finished"] = now.isoformat(timespec="seconds")
    started = _parse(header.get("started"))
    header["duration"] = round((now - started).total_seconds(), 1) if started else 0.0
    path = Path(directory) / RUN_FILE
    path.write_text(json.dumps(header, indent=2), encoding="utf-8")
    return path


def record(directory, report, func: str) -> dict:
    folder = Path(directory) / TESTS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{safe_name(report.nodeid)}.json"
    entry = {}
    if path.exists():
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            entry = {}
    entry.setdefault("nodeid", report.nodeid)
    entry.setdefault("func", func)
    entry.setdefault("status", "passed")
    entry.setdefault("failure", None)
    entry.setdefault("skip_reason", None)
    entry["duration"] = round(entry.get("duration", 0.0) + report.duration, 2)
    entry["last_phase"] = report.when
    if report.failed and entry["status"] != "failed":
        entry["status"] = "failed"
        entry["failure"] = (getattr(report, "longreprtext", "")
                            or str(report.longrepr)).strip()
    elif report.skipped and entry["status"] == "passed":
        entry["status"] = "skipped"
        entry["skip_reason"] = skip_reason(report)
    path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return entry


def read_tests(directory) -> list[dict]:
    """Every test's record. A test still in flight is reported as not verified."""
    folder = Path(directory) / TESTS_DIR
    entries = []
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if entry.pop("last_phase", None) != "teardown" and entry["status"] == "passed":
            entry["status"] = "skipped"
            entry["skip_reason"] = IN_FLIGHT
        entries.append(entry)
    return entries


def skip_reason(report) -> str:
    longrepr = getattr(report, "longrepr", None)
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2]).removeprefix("Skipped: ")
    return ""


def _parse(iso: str):
    try:
        return datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        return None

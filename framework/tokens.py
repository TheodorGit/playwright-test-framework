"""The run's identity: its id, its folder and the label it carries."""

import os
import re
import uuid
from datetime import datetime
from pathlib import Path

RUN_ID_ENV = "QA_RUN_ID"
RESULTS_ENV = "QA_RESULTS_DIR"
LABEL_ENV = "QA_RUN_LABEL"
RUN_ID_PATTERN = r"\d{4}_\d{4}[0-9a-f]{4}"


def new_run_id(now: datetime = None) -> str:
    return f"{(now or datetime.now()):%m%d_%H%M}{uuid.uuid4().hex[:4]}"


def current_run_id() -> str:
    """
    The id every process in this run shares.

    Generated once in the controller and passed on through the
    environment, so pytest-xdist workers report into the same folder.
    """
    run_id = os.environ.get(RUN_ID_ENV)
    if not run_id:
        run_id = new_run_id()
        os.environ[RUN_ID_ENV] = run_id
    return run_id


def results_root() -> Path:
    return Path(os.getenv(RESULTS_ENV, "test_results"))


def run_label() -> str:
    """An optional name for the run, which keeps stored runs apart."""
    return re.sub(r'[<>:"/\|?*\s]+', "_", os.getenv(LABEL_ENV, "")).strip("_.")


def run_dir() -> Path:
    label = run_label()
    name = f"run_{current_run_id()}" + (f"-{label}" if label else "")
    path = results_root() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def newest_run(root: Path = None, marker: str = "run.json") -> Path | None:
    """The most recently finished run under ``root``, for tooling and demos."""
    name = re.compile(rf"run_{RUN_ID_PATTERN}(-.*)?")
    root = Path(root or results_root())
    runs = [p for p in (root.iterdir() if root.is_dir() else [])
            if p.is_dir() and name.fullmatch(p.name) and (p / marker).exists()]
    return max(runs, key=lambda p: (p / marker).stat().st_mtime, default=None)

"""Recorded checks: every check says what it expected before it runs."""

import hashlib
import json
import re
import traceback
from datetime import UTC, datetime
from pathlib import Path

from framework import defects
from framework.reporting.failure_reasons import classify

REASON_MAX = 300
# Windows paths cap near 260 characters, so a long nodeid gets a digest.
NAME_MAX = 120

PASSED, FAILED, SKIPPED, KNOWN_ISSUE = "passed", "failed", "skipped", "known_issue"


def describe(exc: BaseException) -> str:
    """One line a reader can act on: the message, or where it broke."""
    first = next((ln.strip() for ln in str(exc).splitlines() if ln.strip()), "")
    if first:
        return first[:REASON_MAX]
    # A bare assert in a page object carries no message: name the line.
    frames = traceback.extract_tb(exc.__traceback__)
    if frames:
        last = frames[-1]
        code = (last.line or "").strip()
        where = f"{Path(last.filename).name}:{last.lineno}"
        return f"{type(exc).__name__} at {where}" + (f": {code}" if code else "")
    return f"{type(exc).__name__} (no message)"


def full_error(exc: BaseException) -> str:
    text = str(exc).strip()
    return f"{type(exc).__name__}: {text}" if text \
        else f"{type(exc).__name__} (no message)"


def safe_name(nodeid: str) -> str:
    safe = re.sub(r"[^\w.-]+", "_", nodeid).strip("_")
    if len(safe) > NAME_MAX:
        digest = hashlib.sha1(nodeid.encode()).hexdigest()[:8]
        safe = f"{safe[:NAME_MAX]}_{digest}"
    return safe


def _json_safe(value):
    return value if isinstance(value, (str, int, float, bool)) else None


class CheckRecorder:
    """
    The checks one test made, each with what it expected and what it found.

    The report is built from these records, so a check's name and its
    expectation are written for the person reading the report, not for the
    person reading the code.
    """

    def __init__(self, nodeid: str, title: str = "", section: str = ""):
        self.nodeid = nodeid
        self.title = title
        self.section = section
        self.checks: list[dict] = []
        self.metadata: dict = {}
        self.status = "running"
        self._started = datetime.now(UTC)
        self._soft_failures: list[str] = []
        self._watchers: list = []
        self._pending: list[tuple[str, str, bytes]] = []
        self.attachments: dict[int, list[tuple[str, str, bytes]]] = {}

    def attach(self, label: str, content, ext: str = "txt"):
        """Evidence for the check that is running, kept if that check fails."""
        data = content.encode("utf-8") if isinstance(content, str) else bytes(content)
        self._pending.append((label, ext.lstrip("."), data))

    def watch(self, watcher):
        self._watchers.append(watcher)

    def _notify(self, event: str, *args):
        for watcher in self._watchers:
            try:
                getattr(watcher, event)(*args)
            except Exception as exc:
                print(f"[evidence] {type(watcher).__name__}.{event} failed: "
                      f"{type(exc).__name__}: {exc}")

    def _add(self, name: str, status: str, message: str, data: dict,
             expected: str = None, means: str = None, error: str = None,
             defect: str = None, ui: bool = False) -> dict:
        check = {"check": name, "status": status, "message": message,
                 "at": datetime.now(UTC).isoformat(timespec="seconds"),
                 "data": {k: v for k, v in data.items() if v is not None}}
        for key, value in (("expected", expected), ("means", means),
                           ("error", error), ("defect", defect)):
            if value:
                check[key] = value
        if ui:
            check["ui"] = True
        if self._pending:
            self.attachments[len(self.checks) + 1] = self._pending
            check["attachments"] = [f"{label}.{ext}" for label, ext, _ in self._pending]
            self._pending = []
        self.checks.append(check)
        print("[" + status.upper().replace("_", " ") + f"] {name}: {message}")
        self._notify("finished", check, len(self.checks))
        return check

    def step(self, name: str, fn, expected: str = "", means: str = None, found=None,
             ui: bool = False, **data):
        """Runs a check and records it. On failure it records why, then re-raises."""
        self._pending = []
        self._notify("started", name)
        try:
            out = fn()
            said = found(out) if found else expected
        except Exception as exc:
            self._add(name, FAILED, describe(exc), data, expected=expected,
                      means=means or classify(exc), error=full_error(exc), ui=ui)
            raise
        result = _json_safe(out)
        if result is not None:
            data = {**data, "result": result}
        self._add(name, PASSED, said, data, ui=ui)
        return out

    def soft_step(self, name: str, fn, expected: str = "", means: str = None,
                  found=None, ui: bool = False, **data):
        """An independent check: it records its failure and lets the rest run."""
        try:
            return self.step(name, fn, expected, means=means, found=found, ui=ui, **data)
        except Exception as exc:
            self._soft_failures.append(f"{name}: {describe(exc)}")
            return None

    def known_defect(self, name: str, fn, defect: str, expected: str = "",
                     ui: bool = True, **data):
        """
        A check written as the correct behaviour, run against a build where a
        documented defect breaks it.

        The defect still reproducing is recorded as a known issue, with its
        evidence, and the test goes on. The check passing means the defect is
        gone, which fails the test so the check can be promoted into the
        regression suite and its report closed.
        """
        record = defects.get(defect)
        self._pending = []
        self._notify("started", name)
        try:
            fn()
        except Exception as exc:
            self._add(name, KNOWN_ISSUE, describe(exc), data, expected=expected,
                      error=full_error(exc), defect=defect, ui=ui)
            return False
        self._add(name, FAILED, "the check passed, so this defect is gone", data,
                  expected=f"{defect} still reproduces: {record.title}",
                  means="A defect this suite pins no longer reproduces. Promote this "
                        "check into the regression suite and close its report.",
                  defect=defect, ui=ui)
        raise AssertionError(
            f"{defect} no longer reproduces ({name}). Promote this check into the "
            f"regression suite and close docs/defects/{record.doc}.")

    def skip_step(self, name: str, reason: str, expected: str = "", **data):
        """A check this run could not make: reported as not run, never as passed."""
        self._add(name, SKIPPED, reason, data, expected=expected)

    def add_metadata(self, key: str, value):
        self.metadata[key] = value

    def tally(self, key: str, amount: int = 1):
        """Counts what the run actually did, summed into the report's facts."""
        counts = self.metadata.setdefault("tally", {})
        counts[key] = counts.get(key, 0) + amount

    def raise_soft_failures(self):
        if self._soft_failures:
            raise AssertionError(
                f"{len(self._soft_failures)} independent check(s) failed:\n- "
                + "\n- ".join(self._soft_failures))

    def finalize(self, status: str):
        if status == "completed":
            status = "failed" if any(c["status"] == FAILED for c in self.checks) \
                else "passed"
        self.status = status

    @property
    def known_issues(self) -> list[dict]:
        return [c for c in self.checks if c["status"] == KNOWN_ISSUE]

    def to_dict(self) -> dict:
        ended = datetime.now(UTC)
        return {"nodeid": self.nodeid, "title": self.title, "section": self.section,
                "status": self.status,
                "started": self._started.isoformat(timespec="seconds"),
                "ended": ended.isoformat(timespec="seconds"),
                "duration": round((ended - self._started).total_seconds(), 2),
                "checks": self.checks, "metadata": self.metadata}

    def save(self, directory: Path) -> Path:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"checks__{safe_name(self.nodeid)}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str),
                        encoding="utf-8")
        return path

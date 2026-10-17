"""Append a run's verdict to the GitHub job summary.

Usage: python .github/scripts/ci_summary.py "<job title>" [results dir]

Reads the summary.json the suite writes for its newest run, so the job
summary says the same thing as the report attached to the run.
"""

import json
import os
import sys
from pathlib import Path

# Run from anywhere: the repo root is two levels up from this script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from framework import tokens  # noqa: E402


def selected(summary: dict) -> str:
    """What this job was asked to run, so a smaller count is never a mystery."""
    return (summary.get("selection") or {}).get("sentence", "")


def rows(summary: dict) -> list[str]:
    counts = summary["counts"]
    status = ":white_check_mark:" if summary["verdict"] == "passed" else ":x:"
    if summary["verdict"] == "skipped":
        status = ":warning:"
    return [
        f"## {status} {sys.argv[1]}",
        "",
        f"`{summary['subject']}`",
        "",
        selected(summary),
        "",
        "| Tests | Passed | Failed | Not verified | Known issues "
        "| Checks recorded | Duration |",
        "|------:|-------:|-------:|-------------:|-------------:|"
        "----------------:|---------:|",
        f"| {counts['total']} | {counts['passed']} | {counts['failed']} | "
        f"{counts['skipped']} | {counts['known_issues']} | "
        f"{counts['checks_passed']} of {counts['checks_recorded']} passed "
        f"| {summary['duration']}s |",
        "",
    ]


def failures(summary: dict) -> list[str]:
    failed = [t for t in summary["tests"] if t["status"] == "failed"]
    if not failed:
        return []
    lines = ["**Failed:**"]
    lines += [f"- {t['title']} (`{t['nodeid']}`)" for t in failed]
    return lines + [""]


def known_issues(summary: dict) -> list[str]:
    pinned = sorted({defect for test in summary["tests"]
                     for defect in test["known_issues"] if defect})
    if not pinned:
        return []
    return [f"**Known issues still reproducing:** {', '.join(pinned)}", ""]


def main() -> None:
    results = Path(sys.argv[2]) if len(sys.argv) > 2 else tokens.results_root()
    run = tokens.newest_run(results)
    if run is None:
        lines = [f"## :grey_question: {sys.argv[1]}", "",
                 f"No run was recorded under `{results}`.", ""]
    else:
        summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        lines = rows(summary) + failures(summary) + known_issues(summary)
        lines += [f"The full report is attached to this job as an artifact "
                  f"(`{run.name}/report.html`).", ""]
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

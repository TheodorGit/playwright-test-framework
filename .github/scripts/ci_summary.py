"""Append a pass/fail summary for a pytest-json-report file to the GitHub job summary.

Usage: python ci_summary.py <report.json> <job title>
"""

import json
import os
import sys


def main() -> None:
    report_path, title = sys.argv[1], sys.argv[2]

    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    summary = report.get("summary", {})
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    skipped = summary.get("skipped", 0)
    xfailed = summary.get("xfailed", 0)
    duration = report.get("duration", 0.0)

    status = ":white_check_mark:" if failed == 0 else ":x:"
    lines = [
        f"## {status} {title}",
        "",
        "| Total | Passed | Failed | Skipped | Known bugs caught (xfail) | Duration |",
        "|------:|-------:|-------:|--------:|--------------------------:|---------:|",
        f"| {total} | {passed} | {failed} | {skipped} | {xfailed} | {duration:.1f}s |",
        "",
    ]

    failed_tests = [
        t["nodeid"] for t in report.get("tests", []) if t.get("outcome") == "failed"
    ]
    if failed_tests:
        lines.append("**Failed tests:**")
        lines.extend(f"- `{nodeid}`" for nodeid in failed_tests)
        lines.append("")

    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

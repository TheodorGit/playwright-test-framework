"""Builds a run's report, its summary and the email that carries them."""

import html
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from framework import defects, manifest
from framework.reporting import evidence, profiles
from framework.reporting.failure_reasons import classify_failure_text, first_error_line
from framework.reporting.recorder import FAILED, KNOWN_ISSUE, PASSED, SKIPPED

INK, MUTED, LINE, PAGE, ACCENT = "#1F2937", "#6B7280", "#E5E7EB", "#F4F4F7", "#4F46E5"
STATUS = {
    "passed": {"fg": "#15803D", "bg": "#DCFCE7", "label": "PASSED"},
    "failed": {"fg": "#B91C1C", "bg": "#FEE2E2", "label": "FAILED"},
    "skipped": {"fg": "#B45309", "bg": "#FEF3C7", "label": "NOT RUN"},
    "known_issue": {"fg": "#B45309", "bg": "#FEF3C7", "label": "KNOWN ISSUE"},
}


def _esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _duration(seconds) -> str:
    seconds = int(seconds or 0)
    return f"{seconds}s" if seconds < 60 else f"{seconds // 60}m {seconds % 60:02d}s"


def _when(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError):
        return iso or ""


def _check_files(run_dir: Path) -> dict:
    by_nodeid = {}
    for path in sorted(run_dir.glob("checks__*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if data.get("nodeid"):
            by_nodeid[data["nodeid"]] = data
    return by_nodeid


def _evidence(run_dir: Path) -> dict:
    found = {}
    root = run_dir / evidence.EVIDENCE_DIR
    for id_file in sorted(root.glob(f"*/{evidence.ID_FILE}")):
        folder = id_file.parent
        nodeid = id_file.read_text(encoding="utf-8").splitlines()[0].strip()
        rel = f"{evidence.EVIDENCE_DIR}/{folder.name}"
        files: dict = {}
        for item in sorted(folder.iterdir()):
            number, _, rest = item.stem.partition(" ")
            if number.isdigit() and int(number) > 0:
                label = "Screen" if item.suffix == ".png" else f"{rest} ({item.suffix})"
                files.setdefault(int(number), []).append((label, f"{rel}/{item.name}"))
        found[nodeid] = {
            "folder": rel, "files": files,
            "trace": f"{rel}/{evidence.TRACE_FILE}"
                     if (folder / evidence.TRACE_FILE).exists() else None}
    return found


def selection_view(selection: dict, ran: int) -> dict:
    """What the run was asked to run: pytest's own numbers, and one sentence."""
    collected = (selection or {}).get("collected") or 0
    if not collected:
        return {}
    view = {**selection, "ran": ran}
    if view["selected"] == collected:
        sentence = f"All {collected} tests in the suite selected"
    else:
        sentence = (f"{view['selected']} of {collected} tests selected - "
                    f"{view['deselected']} deselected")
        if view.get("expression"):
            sentence += f" by {view['expression']}"
    view["sentence"] = sentence if ran == view["selected"] else f"{sentence} - {ran} ran"
    return view


def load_run(run_dir) -> dict:
    run_dir = Path(run_dir)
    suite = profiles.active()
    header = manifest.read_run(run_dir)
    recorded = _check_files(run_dir)
    kept = _evidence(run_dir)

    tally: dict = {}
    tests = []
    for entry in manifest.read_tests(run_dir):
        nodeid, func = entry["nodeid"], entry["func"]
        profile = profiles.profile_for(nodeid)
        record = recorded.get(nodeid, {})
        checks = record.get("checks", [])
        metadata = record.get("metadata", {})
        for key, value in (metadata.get("tally") or {}).items():
            tally[key] = tally.get(key, 0) + value
        tests.append({
            "nodeid": nodeid, "func": func,
            "title": record.get("title") or profile.title_for(func),
            "section": record.get("section") or profile.section_for(func),
            "number": profile.number_for(func),
            "status": entry["status"], "duration": entry.get("duration", 0),
            "failure": entry.get("failure"), "skip_reason": entry.get("skip_reason"),
            "checks": checks,
            "known_issues": [c for c in checks if c.get("status") == KNOWN_ISSUE],
            "skipped_checks": [(c.get("check", ""), c.get("message", ""))
                               for c in checks if c.get("status") == SKIPPED],
            "metadata": metadata,
            "evidence": kept.get(nodeid),
        })
    tests.sort(key=lambda t: (t["number"] == 0, t["number"], t["title"]))

    counts = {s: sum(1 for t in tests if t["status"] == s)
              for s in ("passed", "failed", "skipped")}
    counts["total"] = len(tests)
    counts["known_issues"] = sum(len(t["known_issues"]) for t in tests)
    counts["skipped_checks"] = sum(len(t["skipped_checks"]) for t in tests)
    # A test with no recorded checks still checked one thing directly. This is
    # what the run recorded, never what it would have recorded: a test that dies
    # at its third check never declares the ones it would have made after it.
    counts["checks_recorded"] = (sum(len(t["checks"]) or 1 for t in tests)
                                 - counts["skipped_checks"])
    counts["checks_passed"] = sum(
        sum(1 for c in t["checks"] if c.get("status") == PASSED) if t["checks"]
        else int(t["status"] == "passed") for t in tests)
    # Checks recorded for a test the run never recorded: the counts understate it.
    known = {t["nodeid"] for t in tests}
    counts["orphan_check_files"] = sorted(n for n in recorded if n not in known)
    verdict = ("failed" if counts["failed"] else
               "skipped" if counts["skipped"] else "passed")
    interrupted = not header.get("finished")

    return {
        "run_id": header.get("run_id"), "started": header.get("started"),
        "finished": header.get("finished") or _last_touched(run_dir),
        "duration": header.get("duration", 0), "label": header.get("label"),
        "environment": header.get("environment"), "interrupted": interrupted,
        "suite_title": suite.title,
        "passed_subhead": suite.passed_subhead,
        "selection": selection_view(manifest.read_selection(run_dir),
                                    counts["total"]),
        "counts": counts, "verdict": verdict, "tests": tests,
        "facts": suite.facts(tally),
        "subject": subject_line(suite.title, verdict, counts,
                                header.get("finished")),
    }


def _last_touched(run_dir: Path) -> str:
    files = list((run_dir / manifest.TESTS_DIR).glob("*.json"))
    if not files:
        return ""
    newest = max(f.stat().st_mtime for f in files)
    return datetime.fromtimestamp(newest, UTC).isoformat(timespec="seconds")


def subject_line(name: str, verdict: str, counts: dict, finished: str) -> str:
    total = counts["total"]
    if verdict == "failed":
        head = f"[FAILED] {name}: {counts['failed']} of {total} tests failed"
    elif verdict == "skipped":
        head = (f"[GAPS] {name}: {counts['passed']} passed, "
                f"{counts['skipped']} not verified")
    else:
        head = f"[PASSED] {name}: all {total} tests passed"
    head += (f" - {counts['checks_passed']} of "
             f"{counts['checks_recorded']} recorded checks passed")
    if counts.get("known_issues"):
        head += f" ({counts['known_issues']} known issue(s))"
    if counts.get("skipped_checks"):
        head += f" ({counts['skipped_checks']} check(s) not run)"
    return head + (f" - {_when(finished)}" if finished else "")


def failure_view(test: dict) -> dict:
    """What to show for a test that failed: its first failed check, or its error."""
    bad = next((c for c in test["checks"] if c.get("status") == FAILED), None)
    if bad:
        return {"check": bad.get("check", ""),
                "means": (bad.get("means") or "").strip(),
                "expected": (bad.get("expected") or "").strip(),
                "instead": (bad.get("message") or "").strip()
                           or first_error_line(test["failure"]),
                "error": (bad.get("error") or "").strip(),
                "defect": bad.get("defect"),
                "stopped": _stopped(test)}
    return {"check": "", "means": classify_failure_text(test["failure"]),
            "expected": "", "instead": first_error_line(test["failure"]),
            "error": "", "defect": None, "stopped": _stopped(test)}


def _stopped(test: dict) -> dict:
    """Where a failed test stopped, so a short list of checks is never a mystery.

    The recorded checks are what the run made, not what the test holds, and
    only the test itself knows the rest. What the report can say is where it
    got to: inside the check that broke, or on an action between checks.
    """
    if test["status"] != "failed" or not test["checks"]:
        return {}
    last = test["checks"][-1]
    if last.get("status") == FAILED:
        # An independent check records its failure and lets the rest run.
        return {} if last.get("soft") else {"number": len(test["checks"]),
                                            "inside": True}
    if last.get("status") == SKIPPED:
        # That check already says it did not run, and says why.
        return {}
    return {"number": len(test["checks"]), "inside": False}


def _stopped_text(stopped: dict) -> str:
    if not stopped:
        return ""
    if stopped["inside"]:
        return (f'The test stopped at check {stopped["number"]}, so whatever it would '
                f'have checked after this one did not run.')
    return (f'The test stopped after check {stopped["number"]}, on an action rather '
            f'than a check, so whatever it would have checked after that did not run.')


def _stopped_note(stopped: dict) -> str:
    text = _stopped_text(stopped)
    return (f'<div style="margin:6px 0 2px;font-size:12px;color:{MUTED};">{text}</div>'
            if text else "")


def _pill(status: str, label: str = None) -> str:
    s = STATUS.get(status, STATUS["skipped"])
    return (f'<span style="display:inline-block;padding:2px 8px;border-radius:999px;'
            f'background:{s["bg"]};color:{s["fg"]};font-size:11px;font-weight:700;'
            f'letter-spacing:.04em;">{_esc(label or s["label"])}</span>')


def _labelled(label: str, value: str) -> str:
    return (f'<div style="margin-top:6px;font-size:13px;color:{INK};">'
            f'<span style="color:{MUTED};font-size:11px;text-transform:uppercase;'
            f'letter-spacing:.05em;">{label}</span> {_esc(value)}</div>')


def _full_error(detail: str) -> str:
    if not detail:
        return ""
    return (f'<details style="margin-top:10px;"><summary style="cursor:pointer;'
            f'font-size:12px;color:{MUTED};">Full error</summary>'
            f'<pre style="white-space:pre-wrap;word-break:break-word;font-size:12px;'
            f'margin:8px 0 0;">{_esc(detail)}</pre></details>')


def _why_box(means: str, expected: str, instead: str, detail: str) -> str:
    s = STATUS["failed"]
    head = (f'<div style="font-weight:600;font-size:14px;">{_esc(means)}</div>'
            if means else "")
    if expected:
        head += _labelled("Expected", expected)
    head += _labelled("Instead", instead)
    return (f'<div style="margin:8px 0 2px;padding:12px;background:{s["bg"]};'
            f'border-radius:4px;"><div style="color:{s["fg"]};font-weight:700;'
            f'font-size:12px;margin-bottom:6px;">WHY IT FAILED</div>{head}'
            f'{_full_error(detail)}</div>')


def _defect_note(defect_id: str) -> str:
    try:
        record = defects.get(defect_id)
    except KeyError:
        return (f'<div style="margin-top:6px;font-size:12px;color:{MUTED};">'
                f'{_esc(defect_id)}, which has no entry in the catalogue</div>')
    return (f'<div style="font-weight:600;font-size:14px;">{_esc(record.title)}</div>'
            f'<div style="margin-top:6px;font-size:12px;color:{MUTED};">'
            f'<a href="{_esc(defects.url(defect_id))}">{_esc(record.id)}, the defect '
            f'report</a> - reproduces on the {_esc(record.build)} build</div>')


def _known_box(check: dict) -> str:
    s = STATUS["known_issue"]
    defect_id = check.get("defect")
    head = (f'<div style="color:{s["fg"]};font-weight:700;font-size:12px;'
            f'margin-bottom:6px;">KNOWN ISSUE'
            f'{" " + _esc(defect_id) if defect_id else ""}</div>')
    body = _defect_note(defect_id) if defect_id else ""
    if check.get("expected"):
        body += _labelled("Expected", check["expected"])
    body += _labelled("Instead", check.get("message"))
    return (f'<div style="margin:8px 0 2px;padding:12px;background:{s["bg"]};'
            f'border-radius:4px;">{head}{body}'
            f'{_full_error((check.get("error") or "").strip())}</div>')


def _note_box(title: str, text: str, status: str) -> str:
    s = STATUS[status]
    return (f'<div style="margin:8px 0 2px;padding:10px;background:{s["bg"]};'
            f'border-radius:4px;font-size:13px;"><b style="color:{s["fg"]};">{title}</b> '
            f'{_esc(text)}</div>')


def _checks_table(test: dict) -> str:
    if not test["checks"]:
        text = {"passed": "No checks recorded: this test asserts directly.",
                "skipped": "No checks recorded: skipped before its first check.",
                }.get(test["status"],
                      "No checks recorded: it failed before its first check.")
        return f'<p style="color:{MUTED};font-size:13px;">{text}</p>'
    rows, first_failure = [], True
    stopped = _stopped(test)
    files = (test.get("evidence") or {}).get("files", {})
    for number, check in enumerate(test["checks"], 1):
        status = check.get("status", SKIPPED)
        cell = ""
        if status == FAILED:
            detail = (check.get("error") or "").strip()
            if first_failure and test["failure"]:
                # The test's own output belongs to the check that broke first.
                detail = f"{detail}\n\n{test['failure']}".strip()
            first_failure = False
            cell += _why_box((check.get("means") or "").strip(),
                             (check.get("expected") or "").strip(),
                             (check.get("message") or "").strip(), detail)
        elif status == KNOWN_ISSUE:
            cell += _known_box(check)
        elif status == SKIPPED:
            cell += _note_box("Not run:", check.get("message"), "skipped")
            if check.get("expected"):
                cell += _labelled("Would have checked", check["expected"])
        else:
            cell += f'<div style="font-size:13px;">{_esc(check.get("message"))}</div>'
        if stopped.get("inside") and number == stopped["number"]:
            cell += _stopped_note(stopped)
        if number in files:
            links = " - ".join(f'<a href="{_esc(quote(path))}">{_esc(label)}</a>'
                               for label, path in files[number])
            cell += (f'<div style="margin-top:4px;font-size:12px;color:{MUTED};">'
                     f'Evidence: {links}</div>')
        td = f'padding:8px;border-bottom:1px solid {LINE};vertical-align:top;'
        rows.append(
            f'<tr><td style="{td}white-space:nowrap;width:1%;">{_pill(status)}</td>'
            f'<td style="{td}width:34%;font-size:13px;">{_esc(check.get("check"))}</td>'
            f'<td style="{td}">{cell}</td></tr>')
    th = (f'padding:6px 8px;border-bottom:2px solid {LINE};text-align:left;'
          f'font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:.05em;'
          f'font-weight:600;')
    head = (f'<thead><tr><th style="{th}"></th><th style="{th}">Check</th>'
            f'<th style="{th}">Result</th></tr></thead>')
    return (f'<table style="width:100%;border-collapse:collapse;margin-top:8px;">'
            f'{head}<tbody>{"".join(rows)}</tbody></table>')


def _test_block(test: dict) -> str:
    status = test["status"]
    opened = " open" if (status != "passed" or test["known_issues"]
                         or test["skipped_checks"]) else ""
    body = ""
    if status == "skipped" and test["skip_reason"]:
        body += _note_box("Not run:", test["skip_reason"], "skipped")
    elif status == "failed" and test["failure"] and not any(
            c.get("status") == FAILED for c in test["checks"]):
        f = failure_view(test)
        body += _why_box(f["means"], f["expected"], f["instead"], test["failure"])
        # It broke between checks, so no check row can carry where it got to.
        body += _stopped_note(f["stopped"])
    video = (test.get("metadata") or {}).get("video")
    if video:
        body += (f'<div style="margin:6px 0;font-size:12px;color:{MUTED};">'
                 f'<a href="{_esc(quote(video))}">Watch this test</a>, a video of what '
                 f'the browser did.</div>')
    kept = test.get("evidence")
    if kept:
        trace = (f' Also: <a href="{_esc(quote(kept["trace"]))}">the trace</a> '
                 f'(open with playwright show-trace).' if kept["trace"] else "")
        body += (f'<div style="margin:6px 0;font-size:12px;color:{MUTED};">Evidence '
                 f'folder: <a href="{_esc(quote(kept["folder"]))}/">'
                 f'{_esc(kept["folder"])}/</a>, files numbered by the check they '
                 f'belong to and listed in test.txt.{trace}</div>')
    checks = test["checks"]
    passed = sum(1 for c in checks if c.get("status") == PASSED)
    count = f"{passed}/{len(checks)} checks" if checks else "no checks"
    number = f'<b style="color:{MUTED};">#{test["number"]}</b> ' if test["number"] else ""
    marks = "".join(" " + _pill("known_issue", c["defect"]) for c in test["known_issues"]
                    if c.get("defect"))
    return (f'<details{opened} style="border:1px solid {LINE};border-radius:6px;'
            f'margin-bottom:8px;background:#fff;"><summary style="padding:10px 12px;'
            f'cursor:pointer;">{_pill(status)} {number}<b>{_esc(test["title"])}</b> '
            f'<span style="color:{MUTED};font-size:12px;">- {count} - '
            f'{_duration(test["duration"])}</span>{marks}</summary>'
            f'<div style="padding:0 12px 12px;"><div style="font-family:Consolas,'
            f'monospace;font-size:11px;color:{MUTED};">{_esc(test["nodeid"])}</div>'
            f'{body}{_checks_table(test)}</div></details>')


def _facts_table(facts: list) -> str:
    if not facts:
        return ""
    cells = "".join(
        f'<td style="padding:10px 14px;text-align:center;border-right:1px solid {LINE};">'
        f'<div style="font-size:20px;font-weight:700;">{_esc(v)}</div>'
        f'<div style="font-size:11px;color:{MUTED};text-transform:uppercase;">'
        f'{_esc(k)}</div></td>' for k, v in facts)
    return (f'<h2 style="font-size:13px;color:{MUTED};text-transform:uppercase;'
            f'margin:24px 0 8px;">What this run actually did</h2>'
            f'<table style="border:1px solid {LINE};background:#fff;'
            f'border-collapse:collapse;"><tr>{cells}</tr></table>')


def _headline(run: dict) -> str:
    c = run["counts"]
    return {"failed": f'{c["failed"]} of {c["total"]} tests failed',
            "skipped": f'{c["passed"]} tests passed, {c["skipped"]} not verified',
            "passed": f'All {c["total"]} tests passed'}[run["verdict"]] \
        + f' - {c["checks_recorded"]} checks recorded'


def _sections_present(tests: list) -> list[str]:
    """The run's own sections, in the profile's order, keeping any it does not name."""
    seen = list(dict.fromkeys(t["section"] for t in tests))
    order = profiles.active().sections_in_order()
    return [s for s in order if s in seen] + [s for s in seen if s not in order]


def render_report(run: dict) -> str:
    v = STATUS[run["verdict"]]
    c = run["counts"]
    present = _sections_present(run["tests"])
    sections = []
    for name in present:
        blocks = "".join(_test_block(t) for t in run["tests"] if t["section"] == name)
        sections.append(f'<h2 style="font-size:13px;color:{MUTED};text-transform:'
                        f'uppercase;margin:24px 0 8px;">{_esc(name)}</h2>{blocks}')
    orphan = ""
    if c["orphan_check_files"]:
        orphan = (f'<p style="color:{STATUS["failed"]["fg"]};">Report integrity: checks '
                  f'were recorded for tests missing from the run record, so the check '
                  f'count understates this run: '
                  f'{_esc(", ".join(c["orphan_check_files"]))}</p>')
    interrupted = (f'<p style="color:{STATUS["failed"]["fg"]};">This run was '
                   f'interrupted; tests still executing are reported as not '
                   f'verified.</p>' if run["interrupted"] else "")
    label = f' - {_esc(run["label"])}' if run.get("label") else ""
    sentence = (run.get("selection") or {}).get("sentence", "")
    selected = (f'<div style="font-size:13px;font-weight:600;color:{INK};'
                f'margin:2px 0 2px;">{_esc(sentence)}</div>' if sentence else "")
    return (
        f'<!doctype html><html><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{_esc(run["suite_title"])} {_esc(run["run_id"])}</title></head>'
        f'<body style="margin:0;background:{PAGE};font-family:-apple-system,Segoe UI,'
        f'Roboto,Arial,sans-serif;color:{INK};"><div style="max-width:960px;'
        f'margin:0 auto;padding:24px;"><div style="border-bottom:2px solid {ACCENT};'
        f'padding-bottom:10px;margin-bottom:16px;font-size:13px;color:{MUTED};">'
        f'<b style="color:{INK};font-size:16px;">{_esc(run["suite_title"])}</b> - run '
        f'{_esc(run["run_id"])}{label} - {_esc(_when(run["finished"]))} - '
        f'{_duration(run["duration"])}</div>'
        f'<div style="background:{v["bg"]};border-radius:8px;padding:16px 18px;">'
        f'<div style="color:{v["fg"]};font-weight:700;font-size:11px;'
        f'letter-spacing:.08em;">{v["label"]}</div>{selected}'
        f'<div style="font-size:22px;font-weight:700;">{_esc(_headline(run))}</div>'
        f'<div style="font-size:13px;color:{MUTED};">{c["passed"]} passed - '
        f'{c["failed"]} failed - {c["skipped"]} not verified - {c["known_issues"]} '
        f'known issue(s) - {c["skipped_checks"]} check(s) not run'
        f'{" - environment " + _esc(run["environment"]) if run["environment"] else ""}'
        f'</div></div>{interrupted}{orphan}{"".join(sections)}'
        f'{_facts_table(run["facts"])}</div></body></html>')


def _email_card(test: dict, bg: str, inner: str) -> str:
    return (f'<tr><td style="padding:6px 24px;"><table width="100%" cellpadding="0" '
            f'cellspacing="0" style="background:{bg};border-radius:4px;"><tr><td '
            f'style="padding:12px 14px;"><div style="font-size:15px;font-weight:600;">'
            f'{_esc(test["title"])}</div>{inner}</td></tr></table></td></tr>')


def _email_heading(text: str, color: str) -> str:
    return (f'<tr><td style="padding:18px 24px 4px;font-size:12px;font-weight:700;'
            f'letter-spacing:.08em;text-transform:uppercase;color:{color};">'
            f'{_esc(text)}</td></tr>')


def _email_known_issues(test: dict) -> str:
    inner = ""
    for check in test["known_issues"]:
        defect_id = check.get("defect")
        name = f"{defect_id}: " if defect_id else ""
        link = ""
        if defect_id and defect_id in defects.CATALOGUE:
            link = f' <a href="{_esc(defects.url(defect_id))}">report</a>'
        inner += (f'<div style="margin-top:6px;font-size:13px;">'
                  f'{_esc(name)}{_esc(check.get("message"))}{link}</div>')
    return inner


def render_email(run: dict) -> str:
    """The stakeholder's view: the verdict, then every failure with its reason."""
    v = STATUS[run["verdict"]]
    counts = run["counts"]
    tests = run["tests"]
    failed = [t for t in tests if t["status"] == "failed"]
    not_verified = [t for t in tests if t["status"] == "skipped"]
    passed = [t for t in tests if t["status"] == "passed"]
    known = [t for t in tests if t["known_issues"]]
    partial = [t for t in tests if t["skipped_checks"]]
    subhead = {"failed": "Failures first, each with the exact check that broke.",
               "skipped": "Nothing failed, but the tests below did not run.",
               "passed": run["passed_subhead"]}[run["verdict"]]
    sentence = (run.get("selection") or {}).get("sentence", "")
    selected = (f'<div style="font-size:13px;font-weight:600;color:{INK};">'
                f'{_esc(sentence)}</div>' if sentence else "")
    blocks = []
    if failed:
        blocks.append(_email_heading(f"Failed ({len(failed)})", STATUS["failed"]["fg"]))
        for test in failed:
            f = failure_view(test)
            inner = ""
            if f["means"]:
                inner += (f'<div style="margin-top:8px;font-size:14px;">'
                          f'{_esc(f["means"])}</div>')
            if f["expected"]:
                inner += _labelled("Expected", f["expected"])
            inner += _labelled("Instead", f["instead"])
            if f["check"]:
                inner += _labelled("Check", f["check"])
            if f["stopped"]:
                inner += (f'<div style="margin-top:6px;font-size:12px;color:{MUTED};">'
                          f'{_esc(_stopped_text(f["stopped"]))}</div>')
            blocks.append(_email_card(test, STATUS["failed"]["bg"], inner))
    if known:
        total_known = counts["known_issues"]
        blocks.append(_email_heading(f"Known issues ({total_known})",
                                     STATUS["known_issue"]["fg"]))
        for test in known:
            blocks.append(_email_card(test, STATUS["known_issue"]["bg"],
                                      _email_known_issues(test)))
    if partial:
        blocks.append(_email_heading("Checks not run", STATUS["skipped"]["fg"]))
        for test in partial:
            inner = "".join(f'<div style="margin-top:6px;font-size:13px;"><b>'
                            f'{_esc(name)}</b> - {_esc(reason)}</div>'
                            for name, reason in test["skipped_checks"])
            blocks.append(_email_card(test, STATUS["skipped"]["bg"], inner))
    if not_verified:
        blocks.append(_email_heading(f"Not verified ({len(not_verified)})",
                                     STATUS["skipped"]["fg"]))
        for test in not_verified:
            reason = test["skip_reason"] or "Not run"
            inner = (f'<div style="margin-top:6px;font-size:13px;">'
                     f'{_esc(reason)}</div>')
            blocks.append(_email_card(test, STATUS["skipped"]["bg"], inner))
    if passed:
        blocks.append(_email_heading(f"Passed ({len(passed)})",
                                     STATUS["passed"]["fg"]))
        rows = "".join(f'<div style="padding:5px 0;font-size:14px;border-bottom:1px '
                       f'solid {LINE};">&#10003; {_esc(t["title"])}</div>'
                       for t in passed)
        blocks.append(f'<tr><td style="padding:2px 24px;">{rows}</td></tr>')
    strip = "".join(f'<td align="center" style="padding:10px 6px;"><div style="'
                    f'font-size:18px;font-weight:700;">{_esc(value)}</div><div style="'
                    f'font-size:10px;color:{MUTED};text-transform:uppercase;">'
                    f'{_esc(name)}</div></td>' for name, value in run["facts"])
    strip_row = ""
    if strip:
        strip_row = (f'<tr><td style="padding:0 24px;"><table width="100%" '
                     f'cellpadding="0" cellspacing="0"><tr>{strip}</tr></table>'
                     f'</td></tr>')
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" style="background:{PAGE};'
        f'font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:{INK};">'
        f'<tr><td align="center" style="padding:20px 10px;"><table width="640" '
        f'cellpadding="0" cellspacing="0" style="width:640px;max-width:100%;'
        f'background:#fff;border:1px solid {LINE};border-radius:8px;">'
        f'<tr><td style="padding:18px 24px;border-bottom:3px solid {ACCENT};'
        f'font-size:16px;font-weight:700;">{_esc(run["suite_title"])}</td></tr>'
        f'<tr><td style="padding:16px 24px;background:{v["bg"]};"><div style="color:'
        f'{v["fg"]};font-size:11px;font-weight:700;letter-spacing:.08em;">'
        f'{v["label"]}</div>{selected}<div style="font-size:20px;font-weight:700;">'
        f'{_esc(_headline(run))}</div><div style="font-size:13px;color:{MUTED};">'
        f'{_esc(subhead)}</div></td></tr>{strip_row}{"".join(blocks)}'
        f'<tr><td style="padding:16px 24px;background:{PAGE};font-size:12px;'
        f'color:{MUTED};">Run {_esc(run["run_id"])} - '
        f'{_esc(_when(run["finished"]))} - {_duration(run["duration"])}. '
        f'The attached report has every check.</td></tr>'
        f'</table></td></tr></table>')


def write_latest(report: Path, page: Path) -> Path:
    """A stable page that opens the newest report, for bookmarks and demos."""
    page = Path(page)
    page.parent.mkdir(parents=True, exist_ok=True)
    target = _esc(quote(Path(os.path.relpath(report, page.parent)).as_posix()))
    page.write_text(
        f'<!doctype html><html><head><meta charset="utf-8">'
        f'<meta http-equiv="refresh" content="0; url={target}">'
        f'<title>Latest report</title></head><body style="font-family:-apple-system,'
        f'Segoe UI,Roboto,Arial,sans-serif;"><p>Opening the latest report: '
        f'<a href="{target}">{target}</a></p></body></html>', encoding="utf-8")
    return page


def _summary(run: dict) -> dict:
    summary = {key: value for key, value in run.items() if key != "tests"}
    rows = []
    for test in run["tests"]:
        passed = sum(1 for c in test["checks"] if c.get("status") == PASSED)
        issues = [c.get("defect") or c.get("check") for c in test["known_issues"]]
        rows.append({"nodeid": test["nodeid"], "title": test["title"],
                     "section": test["section"], "status": test["status"],
                     "duration": test["duration"],
                     "checks_recorded": len(test["checks"]),
                     "checks_passed": passed, "known_issues": issues})
    summary["tests"] = rows
    return summary


def build(run_dir) -> dict:
    """Writes the run's summary, its report and the email, and says where."""
    run_dir = Path(run_dir)
    run = load_run(run_dir)
    (run_dir / "summary.json").write_text(
        json.dumps(_summary(run), indent=2, default=str), encoding="utf-8")
    (run_dir / "report.html").write_text(render_report(run), encoding="utf-8")
    (run_dir / "email.html").write_text(render_email(run), encoding="utf-8")
    return {"verdict": run["verdict"], "subject": run["subject"],
            "report": run_dir / "report.html", "email": run_dir / "email.html",
            "summary": run_dir / "summary.json"}

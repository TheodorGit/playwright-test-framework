"""
The reporting framework, checked without a browser.

These run in milliseconds and guard the part of the suite that nobody
would notice breaking: a report that quietly loses a failure is worse
than no report.

Run them with: pytest framework/tests
"""

import json
from pathlib import Path

import pytest

from framework import defects, manifest
from framework.reporting import report_builder
from framework.reporting.failure_reasons import first_error_line
from framework.reporting.recorder import FAILED, KNOWN_ISSUE, PASSED, CheckRecorder


class FakeReport:
    """What pytest hands the plugin after each phase of a test."""

    def __init__(self, nodeid, when="call", outcome="passed", duration=0.5,
                 failure=""):
        self.nodeid = nodeid
        self.when = when
        self.duration = duration
        self.failed = outcome == "failed"
        self.skipped = outcome == "skipped"
        self.longreprtext = failure
        self.longrepr = failure


def record_test(run_dir, nodeid, func, outcome="passed", failure=""):
    for when in ("setup", "call", "teardown"):
        result = outcome if when == "call" else "passed"
        text = failure if when == "call" else ""
        manifest.record(run_dir, FakeReport(nodeid, when, result, failure=text), func)


def test_a_failed_check_records_what_it_expected_and_what_happened():
    recorder = CheckRecorder("tests/t.py::test_x", "A title", "CHECKOUT")

    def breaks():
        raise AssertionError("the total reads $29.99, the run put in $32.39")

    with pytest.raises(AssertionError):
        recorder.check("the total matches the run", breaks,
                       expected="$32.39, the sum the run read")

    check = recorder.checks[0]
    assert check["status"] == FAILED
    assert check["expected"] == "$32.39, the sum the run read"
    assert check["message"] == "the total reads $29.99, the run put in $32.39"
    assert check["means"] == ("A value the system reported did not match what "
                              "this run did.")


def test_a_defect_that_still_reproduces_is_a_known_issue():
    recorder = CheckRecorder("tests/t.py::test_x", "A title", "KNOWN DEFECTS")

    def breaks():
        raise AssertionError("6 products share 1 image")

    reproduced = recorder.known_defect("every product shows its own image", breaks,
                                       "DEF-01", expected="one image per product")

    assert reproduced is False
    check = recorder.checks[0]
    assert check["status"] == KNOWN_ISSUE
    assert check["defect"] == "DEF-01"
    assert check["message"] == "6 products share 1 image"


def test_a_defect_that_is_fixed_fails_its_test():
    recorder = CheckRecorder("tests/t.py::test_x", "A title", "KNOWN DEFECTS")

    with pytest.raises(AssertionError, match="no longer reproduces"):
        recorder.known_defect("every product shows its own image", lambda: True,
                              "DEF-01", expected="one image per product")

    assert recorder.checks[0]["status"] == FAILED


def test_an_unknown_defect_id_is_refused():
    recorder = CheckRecorder("tests/t.py::test_x", "A title", "KNOWN DEFECTS")

    with pytest.raises(KeyError, match="defect catalogue"):
        recorder.known_defect("something", lambda: True, "DEF-404")


def test_the_report_counts_checks_known_issues_and_links_the_defect(tmp_path):
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")

    passing = CheckRecorder("tests/t.py::test_green", "A green test", "CART")
    passing.check("the cart holds what the run added", lambda: 2,
                  expected="two lines", found=lambda count: f"{count} lines")
    passing.tally("items added", 2)
    passing.finalize("completed")
    passing.save(tmp_path)
    record_test(tmp_path, passing.nodeid, "test_green")

    pinned = CheckRecorder("tests/t.py::test_defect", "A pinned defect",
                           "KNOWN DEFECTS")
    pinned.known_defect("every product shows its own image",
                        lambda: _raise("6 products share 1 image"), "DEF-01",
                        expected="one image per product")
    pinned.finalize("completed")
    pinned.save(tmp_path)
    record_test(tmp_path, pinned.nodeid, "test_defect")

    manifest.finish_run(tmp_path)
    built = report_builder.build(tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    report = (tmp_path / "report.html").read_text(encoding="utf-8")

    assert built["verdict"] == "passed"
    assert summary["counts"]["checks_recorded"] == 2
    assert summary["counts"]["known_issues"] == 1
    assert summary["facts"] == [["items added", 2]]
    assert "DEF-01-product-images-identical.md" in report
    assert "6 products share 1 image" in report
    assert "KNOWN ISSUE" in report


def test_a_run_that_was_killed_reports_its_tests_as_not_verified(tmp_path):
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")
    # Setup and call, but no teardown: the run ended while this test was going.
    for when in ("setup", "call"):
        manifest.record(tmp_path, FakeReport("tests/t.py::test_cut", when), "test_cut")

    run = report_builder.load_run(tmp_path)

    assert run["interrupted"] is True
    assert run["verdict"] == "skipped"
    assert run["tests"][0]["status"] == "skipped"
    assert run["tests"][0]["skip_reason"] == manifest.IN_FLIGHT


def test_a_failure_outside_any_check_still_reaches_the_report(tmp_path):
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")
    failure = "E   playwright._impl._errors.TimeoutError: Locator.click: Timeout"
    record_test(tmp_path, "tests/t.py::test_broken", "test_broken",
                outcome="failed", failure=failure)
    manifest.finish_run(tmp_path)

    run = report_builder.load_run(tmp_path)
    view = report_builder.failure_view(run["tests"][0])

    assert run["verdict"] == "failed"
    assert view["means"] == ("What this check waited for never appeared within "
                             "the timeout.")
    assert "Locator.click" in view["instead"]
    assert run["counts"]["checks_recorded"] == 1
    assert run["counts"]["checks_passed"] == 0


def test_a_passing_test_with_no_checks_still_counts_as_one(tmp_path):
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")
    record_test(tmp_path, "tests/t.py::test_plain", "test_plain")
    manifest.finish_run(tmp_path)

    counts = report_builder.load_run(tmp_path)["counts"]

    assert (counts["checks_recorded"], counts["checks_passed"]) == (1, 1)


def test_the_report_says_how_many_tests_were_selected_and_what_dropped_the_rest(
        tmp_path):
    """A smaller run must never read as tests quietly going missing."""
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")
    manifest.record_selection(tmp_path, collected=43, selected=28,
                              expression='-m "not api and not defect"')
    record_test(tmp_path, "tests/t.py::test_one", "test_one")
    manifest.finish_run(tmp_path)

    report_builder.build(tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    report = (tmp_path / "report.html").read_text(encoding="utf-8")
    email = (tmp_path / "email.html").read_text(encoding="utf-8")

    assert summary["selection"]["collected"] == 43
    assert summary["selection"]["deselected"] == 15
    assert summary["selection"]["ran"] == 1
    sentence = ("28 of 43 tests selected - 15 deselected by -m &quot;not api and "
                "not defect&quot; - 1 ran")
    assert sentence in report
    assert sentence in email


def test_a_run_of_the_whole_suite_says_so(tmp_path):
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")
    manifest.record_selection(tmp_path, collected=1, selected=1)
    record_test(tmp_path, "tests/t.py::test_one", "test_one")
    manifest.finish_run(tmp_path)

    run = report_builder.load_run(tmp_path)

    assert run["selection"]["sentence"] == "All 1 tests in the suite selected"


def test_a_run_with_no_selection_recorded_claims_nothing(tmp_path):
    """Older runs and the framework's own fixtures keep no selection record."""
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")
    record_test(tmp_path, "tests/t.py::test_one", "test_one")
    manifest.finish_run(tmp_path)

    report_builder.build(tmp_path)
    run = report_builder.load_run(tmp_path)
    report = (tmp_path / "report.html").read_text(encoding="utf-8")

    assert run["selection"] == {}
    assert "selected" not in report


def test_a_failed_test_says_its_later_checks_never_ran(tmp_path):
    """The recorded count is not a total, so the report says why it is short."""
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")
    recorder = CheckRecorder("tests/t.py::test_stops", "A test that stops", "CART")
    recorder.check("the first check", lambda: 1, expected="one")
    with pytest.raises(AssertionError):
        recorder.check("the check that broke", lambda: _raise("the badge says 0"),
                       expected="one item in the badge")
    recorder.finalize("failed")
    recorder.save(tmp_path)
    record_test(tmp_path, recorder.nodeid, "test_stops", outcome="failed",
                failure="E   AssertionError: the badge says 0")
    manifest.finish_run(tmp_path)

    report_builder.build(tmp_path)
    report = (tmp_path / "report.html").read_text(encoding="utf-8")
    email = (tmp_path / "email.html").read_text(encoding="utf-8")
    counts = report_builder.load_run(tmp_path)["counts"]

    assert counts["checks_recorded"] == 2
    assert "The test stopped at check 2, so whatever it would have checked" in report
    assert "stopped at check 2" in email
    # No total is claimed anywhere, because the run cannot know one.
    assert "of 2 checks" not in report


def test_a_test_that_broke_between_checks_says_where_it_got_to(tmp_path):
    """Every recorded check passed and the test still failed: on an action."""
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")
    recorder = CheckRecorder("tests/t.py::test_acts", "A test that acts", "CART")
    recorder.check("the only check", lambda: 1, expected="one")
    recorder.finalize("failed")
    recorder.save(tmp_path)
    record_test(tmp_path, recorder.nodeid, "test_acts", outcome="failed",
                failure="E   TimeoutError: Locator.click: Timeout 5000ms exceeded")
    manifest.finish_run(tmp_path)

    report_builder.build(tmp_path)
    report = (tmp_path / "report.html").read_text(encoding="utf-8")
    email = (tmp_path / "email.html").read_text(encoding="utf-8")

    assert "The test stopped after check 1, on an action rather than a check" in report
    assert "stopped after check 1" in email


def test_an_independent_check_that_failed_does_not_claim_the_test_stopped(tmp_path):
    """soft_check lets the rest run, so nothing after it was lost."""
    manifest.start_run(tmp_path, "0101_00000000", "chromium, headless")
    recorder = CheckRecorder("tests/t.py::test_soft", "A test with soft checks", "CART")
    recorder.soft_check("an independent check", lambda: _raise("one reading is off"),
                        expected="every reading in agreement")
    recorder.finalize("failed")
    recorder.save(tmp_path)
    record_test(tmp_path, recorder.nodeid, "test_soft", outcome="failed",
                failure="E   AssertionError: 1 independent check(s) failed")
    manifest.finish_run(tmp_path)

    report_builder.build(tmp_path)

    assert "stopped at check" not in (tmp_path / "report.html").read_text(
        encoding="utf-8")


def test_check_statuses_are_the_ones_the_report_knows():
    assert set(report_builder.STATUS) >= {PASSED, FAILED, KNOWN_ISSUE, "skipped"}


def test_every_pinned_defect_has_a_report_to_link_to():
    """A catalogue entry without its document would link the report nowhere."""
    docs = Path(__file__).resolve().parents[2] / "docs" / "defects"
    missing = [d.id for d in defects.pinned() if not (docs / d.doc).exists()]

    assert not missing, f"no report under docs/defects for: {missing}"


def test_a_failure_reason_drops_the_assertion_class_but_keeps_others():
    """The report prints a reason, not an exception name the reader cannot use."""
    assertion = first_error_line("E   AssertionError: the badge says 0, expected 1")
    timeout = first_error_line("E   TimeoutError: waiting for get_by_role('button')")

    assert assertion == "the badge says 0, expected 1"
    assert timeout.startswith("TimeoutError:")


def _framework_sources() -> list[Path]:
    """Every framework module except its own tests and the one product seam."""
    root = Path(__file__).resolve().parents[1]
    return [f for f in sorted(root.rglob("*.py"))
            if "tests" not in f.parts and f.name != "defects.py"]


def _reaches_for(text: str, package: str) -> bool:
    opening = (f"import {package}", f"from {package}")
    return any(line.strip().startswith(opening) for line in text.splitlines())


def _quoted_test_names(text: str) -> list[str]:
    """Test function names written into the source as string literals."""
    found = set()
    for quote in ("'", '"'):
        for tail in text.split(quote + "test_")[1:]:
            name = "test_" + tail.split(quote)[0]
            # test_results is the results directory, not a test.
            if name != "test_results":
                found.add(name)
    return sorted(found)


def test_the_framework_does_not_import_the_suite_it_runs():
    """framework/ stays reusable only while it knows nothing of pages/ or tests/."""
    reaching = {f.name for f in _framework_sources()
                for package in ("pages", "tests")
                if _reaches_for(f.read_text(encoding="utf-8"), package)}

    assert not reaching, f"framework modules importing the suite: {sorted(reaching)}"


def test_the_framework_names_no_test_of_the_suite_it_runs():
    """A hardcoded test name is a second product seam: it belongs in the suite."""
    named = {f.name: _quoted_test_names(f.read_text(encoding="utf-8"))
             for f in _framework_sources()}
    offenders = {name: hits for name, hits in named.items() if hits}

    assert not offenders, f"framework modules naming suite tests: {offenders}"


def _raise(message: str):
    raise AssertionError(message)

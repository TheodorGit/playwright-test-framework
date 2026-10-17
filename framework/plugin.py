"""The framework's pytest plugin: the run folder, the checks, the report."""

import os
from pathlib import Path

import pytest

from framework import manifest, tokens
from framework.reporting import evidence, profiles
from framework.reporting.recorder import CheckRecorder

ENVIRONMENT_ENV = "QA_ENVIRONMENT"
LATEST_PAGE_ENV = "QA_LATEST_PAGE"
LAST_IN_THE_PLAN = 10 ** 6


def environment() -> str:
    """What this run drove, as the report prints it."""
    return os.getenv(ENVIRONMENT_ENV, "")


def is_worker(config) -> bool:
    return hasattr(config, "workerinput")


def pytest_configure(config):
    # Fixes the id before pytest-xdist starts its workers, which inherit it.
    tokens.current_run_id()
    if not is_worker(config):
        manifest.start_run(tokens.run_dir(), tokens.current_run_id(),
                           environment(), tokens.run_label())


def pytest_report_header(config):
    return f"run {tokens.current_run_id()} in {tokens.run_dir().as_posix()}"


def pytest_collection_modifyitems(config, items):
    """Runs the suite in the order the report presents it."""
    items.sort(key=lambda item: profiles.number_for(_func(item)) or LAST_IN_THE_PLAN)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    # Exposed so fixtures can read the outcome while tearing down.
    setattr(item, f"rep_{report.when}", report)
    manifest.record(tokens.run_dir(), report, _func(item))


def pytest_sessionfinish(session, exitstatus):
    if is_worker(session.config):
        return
    directory = tokens.run_dir()
    try:
        manifest.read_run(directory)
    except FileNotFoundError:
        return
    if not manifest.read_tests(directory):
        # Nothing ran, as after a collection: leave no empty run behind.
        _discard_if_empty(directory)
        return
    manifest.finish_run(directory)
    try:
        from framework.reporting import report_builder
        built = report_builder.build(directory)
        latest = report_builder.write_latest(built["report"], latest_page())
    except Exception as exc:  # a bug in the report must not change the verdict
        print(f"\n[report] could not build the report: {type(exc).__name__}: {exc}")
        return
    subject = built["subject"]
    print(f"\n[report] {subject}")
    print(f"[report] {_shown(built['report'])}")
    print(f"[report] latest: {_shown(latest)}")


def _discard_if_empty(directory: Path):
    run_file = directory / manifest.RUN_FILE
    if [p.name for p in directory.iterdir()] != [run_file.name]:
        return
    run_file.unlink()
    directory.rmdir()


def latest_page() -> Path:
    return Path(os.getenv(LATEST_PAGE_ENV) or tokens.results_root() / "latest.html")


def _func(item) -> str:
    return getattr(item, "originalname", None) or item.name.split("[")[0]


def _shown(path) -> str:
    try:
        return Path(os.path.relpath(path)).as_posix()
    except ValueError:  # another drive on Windows: nothing relative to show
        return str(path)


@pytest.fixture(scope="session")
def run_id() -> str:
    return tokens.current_run_id()


@pytest.fixture
def steps(request):
    """
    The checks this test records.

    Saved whatever the outcome, so a failing or interrupted test still
    reports what it had checked by then, and the independent checks it
    recorded with soft_step are raised together here.
    """
    func = _func(request.node)
    recorder = CheckRecorder(request.node.nodeid, profiles.title_for(func),
                             profiles.section_for(func))
    yield recorder
    setup = getattr(request.node, "rep_setup", None)
    call = getattr(request.node, "rep_call", None)
    skipped = ((setup is not None and setup.skipped)
               or (call is not None and call.skipped))
    if skipped:
        recorder.finalize("skipped")
    else:
        passed = call is not None and call.passed
        recorder.finalize("completed" if passed else "failed")
    recorder.save(tokens.run_dir())
    evidence.save_attachments(recorder, tokens.run_dir())
    if call is not None and call.passed:
        recorder.raise_soft_failures()

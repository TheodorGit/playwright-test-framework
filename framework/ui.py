"""Videos, traces and per-check screens of the browser tests."""

import os
from pathlib import Path

from framework.reporting import evidence
from framework.reporting.recorder import FAILED, KNOWN_ISSUE, CheckRecorder

TRACE_FILE = evidence.TRACE_FILE
VIDEOS_DIR = "videos"
KEEP_VIDEOS_ENV = "QA_KEEP_VIDEOS"
NO_PAGE = ("", "about:blank")
BAD = (FAILED, KNOWN_ISSUE)


class BrowserEvidence:
    """
    Watches a test's checks and keeps what a reader would need to see.

    Screens are taken after every check that touched the page, the trace
    covers the whole test with one group per check, and both are kept when
    a check failed or found a known defect.
    """

    def __init__(self, context, page, recorder: CheckRecorder):
        self.context = context
        self.page = page
        self.recorder = recorder
        self.shots: list[tuple[str, bytes]] = []
        self._last: bytes | None = None
        self._group_open = False
        context.tracing.start(title=evidence.title_of(recorder), screenshots=True,
                              snapshots=True, sources=True)
        recorder.watch(self)

    def started(self, name: str):
        self._close_group()
        self.context.tracing.group(name)
        self._group_open = True

    def finished(self, check: dict, number: int):
        self._close_group()
        if not check.get("ui") or self.page.url in NO_PAGE:
            return
        try:
            png = self.page.screenshot()
        except Exception as exc:
            print(f"[evidence] screenshot after check {number} failed: "
                  f"{type(exc).__name__}: {exc}")
            return
        # An unchanged screen says nothing, unless it is the screen that broke.
        if png == self._last and check.get("status") not in BAD:
            return
        self._last = png
        self.shots.append((evidence.check_file(number), png))

    def _close_group(self):
        if self._group_open:
            self._group_open = False
            self.context.tracing.group_end()

    def needed(self, test_failed: bool) -> bool:
        checks = self.recorder.checks
        ui_bad = any(c.get("ui") and c.get("status") in BAD for c in checks)
        nothing_recorded = not any(c.get("status") == FAILED for c in checks)
        return ui_bad or (test_failed and nothing_recorded)

    def stop(self, run_dir, test_failed: bool) -> Path | None:
        self._close_group()
        keep = self.needed(test_failed)
        folder = evidence.folder_for(self.recorder, run_dir) if keep else None
        self.context.tracing.stop(path=str(folder / TRACE_FILE) if keep else None)
        video = getattr(self.page, "video", None)
        # Playwright only writes the video once the context is closed.
        self.context.close()
        if video is not None:
            self._keep_video(video, Path(run_dir), keep)
        if keep:
            for name, png in self.shots:
                (folder / name).write_bytes(png)
        return folder

    def _keep_video(self, video, run_dir: Path, keep: bool):
        if not (keep or keep_all_videos()):
            video.delete()
            return
        folder = run_dir / VIDEOS_DIR
        folder.mkdir(parents=True, exist_ok=True)
        base = evidence.folder_name(self.recorder)
        target, n = folder / f"{base}.webm", 2
        while target.exists():
            target, n = folder / f"{base}_{n}.webm", n + 1
        video.save_as(str(target))
        video.delete()
        self.recorder.add_metadata("video", f"{VIDEOS_DIR}/{target.name}")


def keep_all_videos() -> bool:
    return os.getenv(KEEP_VIDEOS_ENV, "").strip().lower() in ("1", "all", "true", "yes")


def failed(recorder: CheckRecorder, node) -> bool:
    phases = any(getattr(getattr(node, f"rep_{when}", None), "failed", False)
                 for when in ("setup", "call"))
    return phases or any(c.get("status") == FAILED for c in recorder.checks)

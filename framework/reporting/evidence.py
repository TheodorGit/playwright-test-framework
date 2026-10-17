"""
A test's evidence folder and the names of the files in it.

Files are numbered by the check they belong to, and ``test.txt`` lists the
checks in order, so a reader can tell which screenshot answers which
check without opening them all.
"""

import re
from pathlib import Path

from framework.reporting import profiles
from framework.reporting.recorder import (FAILED, KNOWN_ISSUE, SKIPPED,
                                          CheckRecorder, safe_name)

EVIDENCE_DIR = "evidence"
ID_FILE = "test.txt"
TRACE_FILE = "00 trace.zip"
LABEL_MAX = 50
KEPT = (FAILED, KNOWN_ISSUE)
_UNSAFE = re.compile(r'[<>:"/\|?*\x00-\x1f]+')


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", _UNSAFE.sub("_", text or "")).strip(" ._")


def middle(text: str, limit: int) -> str:
    """Shortens from the middle, so both ends of a label stay readable."""
    if len(text) <= limit:
        return text
    head, tail = limit // 2, (limit - 1) // 2
    return f"{text[:head].rstrip()}~{text[len(text) - tail:].lstrip()}"


def check_file(number: int, label: str = "screen", ext: str = "png") -> str:
    return f"{number:02d} {middle(clean(label), LABEL_MAX) or 'file'}.{ext}"


def func_of(recorder: CheckRecorder) -> str:
    return recorder.nodeid.split("::")[-1].split("[")[0]


def folder_name(recorder: CheckRecorder) -> str:
    return safe_name(func_of(recorder))


def title_of(recorder: CheckRecorder) -> str:
    return recorder.title or profiles.title_for(func_of(recorder))


def write_index(recorder: CheckRecorder, folder: Path):
    # The report matches on the first line, the nodeid.
    lines = [recorder.nodeid, title_of(recorder)]
    for number, check in enumerate(recorder.checks, 1):
        result = (check.get("status") or SKIPPED).upper().replace("_", " ")
        lines.append(f"{number:02d}  {result}  {check.get('check', '')}")
    (folder / ID_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")


def folder_for(recorder: CheckRecorder, run_dir: Path) -> Path:
    existing = getattr(recorder, "_evidence_folder", None)
    if existing is not None:
        return existing
    root = Path(run_dir) / EVIDENCE_DIR
    base = folder_name(recorder)
    folder, n = root / base, 2
    while folder.exists():
        folder, n = root / f"{base}_{n}", n + 1
    folder.mkdir(parents=True)
    write_index(recorder, folder)
    recorder._evidence_folder = folder
    return folder


def save_attachments(recorder: CheckRecorder, run_dir: Path) -> list[Path]:
    """Writes the evidence of the checks that failed or found a known defect."""
    written = []
    for number, items in sorted(recorder.attachments.items()):
        if recorder.checks[number - 1].get("status") not in KEPT:
            continue
        folder = folder_for(recorder, run_dir)
        for label, ext, content in items:
            path = folder / check_file(number, label, ext)
            path.write_bytes(content)
            written.append(path)
    folder = getattr(recorder, "_evidence_folder", None)
    if folder is not None:
        write_index(recorder, folder)
    return written

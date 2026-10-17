#!/usr/bin/env python3
"""Run the pinned GameGen-Verifier harness on Windows.

Why this exists
---------------
``harness/run_normal_eval.py`` starts the game with

    [str(workspace/".codex/skills/auto-eval/scripts/dev_server_lifecycle.sh"), "start", ...]

Windows ``CreateProcess`` cannot execute a ``.sh`` file, so the pinned harness
fails with ``[WinError 193]`` before any browser work happens. This launcher
leaves the pinned checkout untouched and only translates that one POSIX
invocation into ``bash <script> <args...>`` for the duration of the harness
process. Everything else (backend command, ``python3`` helpers, artifact
validation) is passed through unchanged.

Usage:
    python windows_posix_shim.py <path-to-run_normal_eval.py> [harness args...]
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
)


def find_bash() -> str:
    for candidate in _BASH_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    found = shutil.which("bash")
    if not found:
        raise SystemExit("bash not found; the GameGen-Verifier lifecycle script requires it")
    return found


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)

    harness = Path(sys.argv[1]).resolve()
    harness_args = sys.argv[2:]
    if not harness.is_file():
        raise SystemExit(f"harness script not found: {harness}")

    bash = find_bash()
    real_popen = subprocess.Popen

    def posix_aware_popen(args, *rest, **kwargs):  # type: ignore[no-untyped-def]
        command = args if isinstance(args, (list, tuple)) else [args]
        if command and str(command[0]).lower().endswith(".sh"):
            translated = [bash, str(command[0]), *[str(item) for item in command[1:]]]
            environment = kwargs.get("env") or os.environ.copy()
            environment.setdefault("MSYSTEM", "MINGW64")
            kwargs["env"] = environment
            return real_popen(translated, *rest, **kwargs)
        return real_popen(args, *rest, **kwargs)

    subprocess.Popen = posix_aware_popen  # type: ignore[assignment]

    sys.argv = [str(harness), *harness_args]
    source = harness.read_text(encoding="utf-8")
    globals_dict = {"__name__": "__main__", "__file__": str(harness), "__builtins__": __builtins__}
    exec(compile(source, str(harness), "exec"), globals_dict)  # noqa: S102 - pinned harness entry point
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

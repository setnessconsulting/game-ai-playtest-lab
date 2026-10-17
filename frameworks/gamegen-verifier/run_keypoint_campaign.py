#!/usr/bin/env python3
"""Run the five locked GAME-311 keypoints through the pinned GameGen-Verifier harness.

The harness is used unmodified: this script only assembles the documented
command line. Two documented harness behaviours make the five-keypoint
campaign possible without touching the pinned checkout:

* ``--keypoints-md`` is not needed because the workspace
  ``games/number_line_jumper/keypoints.md`` is the source of truth;
* ``--resume-run`` plus a pre-seeded
  ``runs/<game>/<run_id>/keypoints.snapshot.md`` is the framework's documented
  resume path, which reuses an already-frozen keypoint set instead of
  re-distilling 30-40 keypoints from a game description. ``--min-keypoints 5``
  lowers the count gate that the resume path still enforces.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK_SCRIPT_DIR = Path(__file__).resolve().parent
GAME_NAME = "number_line_jumper"
DEFAULT_FRAMEWORK = LAB_ROOT / ".frameworks" / "gamegen-verifier"
DEFAULT_WORKSPACE = LAB_ROOT / ".frameworks" / "ggv-workspace"
DEFAULT_PYTHON3 = LAB_ROOT / ".frameworks" / "ggv-venv" / "Scripts"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework-root", type=Path, default=DEFAULT_FRAMEWORK)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--backend", default="codex", choices=["codex", "claude"])
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--model", default="")
    parser.add_argument("--step-timeout", type=int, default=1800)
    parser.add_argument("--screenshot-mode", default="sequence")
    parser.add_argument("--screenshot-interval", type=int, default=200)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--keypoints-per-session", type=int, default=1)
    parser.add_argument("--only-keypoints", default="", help="Comma-separated keypoint ids.")
    parser.add_argument("--min-keypoints", type=int, default=5)
    parser.add_argument("--python3-bin", type=Path, default=DEFAULT_PYTHON3)
    parser.add_argument(
        "--codex-bin",
        type=Path,
        default=None,
        help="Directory or executable on PATH containing the authenticated codex CLI "
        "(default: whatever `codex` resolves to in the current PATH).",
    )
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()

    framework = args.framework_root.resolve()
    workspace = args.workspace.resolve()
    run_dir = workspace / "runs" / GAME_NAME / args.run_id
    if not (run_dir / "keypoints.snapshot.md").is_file():
        raise SystemExit(
            f"missing pre-seeded keypoint snapshot: {run_dir / 'keypoints.snapshot.md'}\n"
            "run prepare_workspace.py first"
        )

    harness = str(framework / "harness" / "run_normal_eval.py")
    if sys.platform == "win32":
        # Windows cannot exec the harness's POSIX dev-server lifecycle script.
        # windows_posix_shim.py translates only that one call and leaves the
        # pinned checkout untouched. See its module docstring.
        command = [
            sys.executable,
            str(FRAMEWORK_SCRIPT_DIR / "windows_posix_shim.py"),
            harness,
        ]
    else:
        command = [sys.executable, harness]
    command += [
        "--workspace",
        str(workspace),
        "--game-name",
        GAME_NAME,
        "--run-id",
        args.run_id,
        "--backend",
        args.backend,
        "--reasoning-effort",
        args.reasoning_effort,
        "--screenshot-mode",
        args.screenshot_mode,
        "--screenshot-interval",
        str(args.screenshot_interval),
        "--max-workers",
        str(args.max_workers),
        "--keypoints-per-session",
        str(args.keypoints_per_session),
        "--min-keypoints",
        str(args.min_keypoints),
        "--step-timeout",
        str(args.step_timeout),
        "--resume-run",
    ]
    if args.model:
        command.extend(["--model", args.model])
    if args.only_keypoints:
        command.extend(["--only-keypoints", args.only_keypoints])

    python3_bin = args.python3_bin.resolve()
    if not (python3_bin / "python3.exe").is_file() and not (python3_bin / "python3").is_file():
        raise SystemExit(
            f"python3 shim missing in {python3_bin}: the harness shells out to `python3`\n"
            "see frameworks/gamegen-verifier/README.md step 2"
        )

    if args.codex_bin is not None:
        codex_bin = args.codex_bin.resolve()
        if not codex_bin.exists():
            raise SystemExit(f"codex path not found: {codex_bin}")
        codex_dir = codex_bin if codex_bin.is_dir() else codex_bin.parent
    else:
        found = shutil.which(args.backend)
        if not found:
            raise SystemExit(
                f"`{args.backend}` is not on PATH; pass --codex-bin with the directory "
                "containing the authenticated CLI"
            )
        codex_dir = Path(found).resolve().parent

    environment = dict(os.environ)
    prepend = [str(python3_bin), str(codex_dir)]
    environment["PATH"] = os.pathsep.join(prepend + [environment.get("PATH", "")])

    log_path = run_dir / "campaign.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "command": command,
        "cwd": str(framework),
        "path_prepended": prepend,
        "log": str(log_path),
    }
    print(json.dumps(record, indent=2))
    if args.plan_only:
        return 0

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.run(
            command,
            cwd=str(framework),
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())

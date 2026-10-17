#!/usr/bin/env python3
"""Materialize the GameGen-Verifier evaluation workspace for the frozen game.

The pinned framework expects a workspace containing ``descriptions_example/``,
``games/<game>/``, ``.codex/skills/`` and ``tools/playwright/``. This script
builds that workspace outside the pinned checkout so the framework revision
stays pristine. It fails closed when either pinned revision does not match the
GAME-308 contract in ``config/experiment.json``.

Only the standard library is used.
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
FRAMEWORK_DIR = Path(__file__).resolve().parent
WORKSPACE_TEMPLATE = FRAMEWORK_DIR / "workspace"
GAME_NAME = "number_line_jumper"


def load_contract() -> dict:
    contract = json.loads((LAB_ROOT / "config" / "experiment.json").read_text(encoding="utf-8"))
    return contract["experiment"]


def git_revision(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, encoding="utf-8"
    ).strip()


def link_dir(link: Path, target: Path) -> None:
    """Create a directory junction/symlink, replacing any existing link."""
    if link.exists() or link.is_symlink():
        try:
            # Removes a junction/symlink itself without touching its target.
            os.rmdir(link)
        except OSError:
            if link.is_dir():
                shutil.rmtree(link)
            else:
                link.unlink()
    link.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise SystemExit(f"failed to create junction {link} -> {target}: {result.stderr.strip()}")
    else:
        link.symlink_to(target, target_is_directory=True)


def copy_template(destination: Path) -> None:
    for source in sorted(WORKSPACE_TEMPLATE.rglob("*")):
        if source.is_dir():
            continue
        relative = source.relative_to(WORKSPACE_TEMPLATE)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--framework-root",
        type=Path,
        default=LAB_ROOT / ".frameworks" / "gamegen-verifier",
        help="Path of the pinned GameGen-Verifier checkout.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=LAB_ROOT / ".frameworks" / "ggv-workspace",
        help="Path of the workspace to (re)build.",
    )
    parser.add_argument(
        "--frozen-game-root",
        type=Path,
        required=True,
        help="Path of a clean worktree of the frozen Number Line Jumper revision.",
    )
    parser.add_argument("--run-id", default="ggv-nlj-keypoints-1")
    args = parser.parse_args()

    experiment = load_contract()
    game_revision = experiment["game"]["revision"]
    framework_revision = experiment["frameworks"]["gamegen-verifier"]["revision"]

    framework = args.framework_root.resolve()
    frozen = args.frozen_game_root.resolve()
    workspace = args.workspace.resolve()

    if not (framework / "harness" / "run_normal_eval.py").is_file():
        raise SystemExit(f"framework checkout missing: {framework}")
    if not (frozen / "package.json").is_file():
        raise SystemExit(f"frozen game worktree missing: {frozen}")

    actual_framework = git_revision(framework)
    if actual_framework != framework_revision:
        raise SystemExit(
            f"GameGen-Verifier revision mismatch: workspace has {actual_framework}, "
            f"GAME-308 pins {framework_revision}"
        )
    actual_game = git_revision(frozen)
    if actual_game != game_revision:
        raise SystemExit(
            f"game revision mismatch: worktree has {actual_game}, GAME-308 pins {game_revision}"
        )

    dirty = subprocess.run(
        ["git", "-C", str(frozen), "status", "--porcelain"], capture_output=True, text=True
    ).stdout.strip()
    if dirty:
        raise SystemExit(f"frozen game worktree is not clean:\n{dirty}")

    copy_template(workspace)
    # The framework's worker-side scripts derive the repository root from their
    # own path (`.codex/skills/<orchestrator>/scripts/...` -> parents[4]). Windows
    # junctions are resolved by pathlib, so a junction for `.codex/skills` would
    # make that arithmetic land one level too high. The skills are therefore
    # copied byte-for-byte from the pinned checkout instead of linked.
    skills_target = workspace / ".codex" / "skills"
    if skills_target.exists() or skills_target.is_symlink():
        try:
            os.rmdir(skills_target)
        except OSError:
            shutil.rmtree(skills_target)
    shutil.copytree(framework / "skills", skills_target)
    link_dir(workspace / "scripts", framework / "scripts")
    link_dir(workspace / "tools", framework / "tools")
    link_dir(workspace / "games" / GAME_NAME / "src", frozen / "src")

    game_dir = workspace / "games" / GAME_NAME
    (game_dir / "frozen-root.json").write_text(
        json.dumps({"frozen_root": str(frozen)}, indent=2) + "\n", encoding="utf-8"
    )

    run_dir = workspace / "runs" / GAME_NAME / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(game_dir / "keypoints.md", run_dir / "keypoints.snapshot.md")
    manifest = {
        "game_name": GAME_NAME,
        "game_revision": game_revision,
        "framework_revision": framework_revision,
        "framework_root": str(framework),
        "frozen_game_root": str(frozen),
        "workspace": str(workspace),
        "run_id": args.run_id,
    }
    (run_dir / "prepare_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

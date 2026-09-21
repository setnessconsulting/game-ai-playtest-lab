from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .core import (
    ContractError,
    FRAMEWORKS,
    PERSONAS,
    RUNNERS,
    build_plan,
    check_game_reachable,
    load_experiment,
    repo_root,
    validate_finding_file,
)


def _json_dump(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def cmd_validate(_: argparse.Namespace) -> int:
    root = repo_root()
    exp = load_experiment(root)
    sample = root / "reports" / "examples" / "sample-finding.json"
    validate_finding_file(sample)
    print(f"contract: ok ({exp['id']})")
    print("sample finding: ok")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    plan = build_plan(
        framework=args.framework,
        persona=args.persona,
        runner=args.runner,
        model=args.model,
        game_url=args.game_url,
    )
    output = _json_dump(plan.as_dict())
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        print(path)
    else:
        print(output, end="")
    return 0


def cmd_validate_finding(args: argparse.Namespace) -> int:
    validate_finding_file(Path(args.path))
    print(f"finding: ok ({args.path})")
    return 0


def cmd_check_game(args: argparse.Namespace) -> int:
    url, status = check_game_reachable(args.game_url, timeout=args.timeout)
    print(f"game: reachable ({status}) {url}")
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    root = repo_root()
    exp = load_experiment(root)
    validate_finding_file(root / "reports" / "examples" / "sample-finding.json")

    statuses = {}
    for runner in RUNNERS:
        executable = exp["runners"][runner]["executable"]
        statuses[runner] = shutil.which(executable)

    print("contract: ok")
    print("sample finding: ok")
    for runner in RUNNERS:
        path = statuses[runner]
        print(f"runner {runner}: {'found at ' + path if path else 'not found on PATH'}")

    if args.check_game:
        url, status = check_game_reachable(args.game_url, timeout=args.timeout)
        print(f"game: reachable ({status}) {url}")

    if args.require_runner and not statuses[args.require_runner]:
        print(f"required runner unavailable: {args.require_runner}", file=sys.stderr)
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="playtest-lab",
        description="Validate and plan the bounded GAME-308 AI playtest experiment.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate the frozen experiment contract and sample finding.")
    p_validate.set_defaults(func=cmd_validate)

    p_plan = sub.add_parser("plan", help="Emit a normalized run plan without invoking an AI framework.")
    p_plan.add_argument("--framework", required=True, choices=FRAMEWORKS)
    p_plan.add_argument("--persona", required=True, choices=PERSONAS)
    p_plan.add_argument("--runner", default="codex", choices=RUNNERS)
    p_plan.add_argument("--model", help="Optional runtime model identifier; never persisted into the frozen config.")
    p_plan.add_argument("--game-url", help="Override the default local game URL for this run only.")
    p_plan.add_argument("--output", help="Optional path for the generated JSON plan.")
    p_plan.set_defaults(func=cmd_plan)

    p_finding = sub.add_parser("validate-finding", help="Validate a normalized finding JSON file.")
    p_finding.add_argument("path")
    p_finding.set_defaults(func=cmd_validate_finding)

    p_game = sub.add_parser("check-game", help="Verify that the configured Number Line Jumper URL is reachable.")
    p_game.add_argument("--game-url", help="Override the configured game URL for this check.")
    p_game.add_argument("--timeout", type=float, default=5.0)
    p_game.set_defaults(func=cmd_check_game)

    p_smoke = sub.add_parser("smoke", help="Validate contract and report local runner CLI availability.")
    p_smoke.add_argument("--require-runner", choices=RUNNERS)
    p_smoke.add_argument("--check-game", action="store_true", help="Also require the game URL to respond.")
    p_smoke.add_argument("--game-url", help="Override the configured game URL when --check-game is used.")
    p_smoke.add_argument("--timeout", type=float, default=5.0)
    p_smoke.set_defaults(func=cmd_smoke)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ContractError as exc:
        print(f"contract error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

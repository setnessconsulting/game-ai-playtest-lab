"""Bounded native-contract GameWorld run using OpenCode Go.

The runner uses the pinned GameWorld browser manager, semantic-control tool
schema, and action executor.  Only the provider adapter is lab-local, so the
frozen upstream checkout and the frozen game build remain unchanged.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any


LAB_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GAMEWORLD_ROOT = LAB_ROOT / ".frameworks" / "gameworld-upstream"
DEFAULT_CHROME = Path(
    os.environ.get(
        "GAMEWORLD_CHROME_PATH",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
    )
)
DEFAULT_MODEL = "deepseek-v4.1-flash"
DEFAULT_ENDPOINT = "https://opencode.ai/zen/go/v1/chat/completions"
DEFAULT_REASONING_EFFORT = "max"
DEFAULT_TOOL_CHOICE = "auto"
DEFAULT_PROTOCOL = "chat_completions"
GAME_SHA = "47a05480d7c32cee8f0991d6f6c0410be90d678e"
GAMEWORLD_SHA = "3c26bdab436800fd61ef40543b64ca40d12c7e4a"
MATH_DETECTIVE_RELEASE = "2026.09.21-playtest-enhancements.1"
MATH_DETECTIVE_URL = (
    "https://games.setnessconsulting.com/game-assets/math-detective/"
    f"{MATH_DETECTIVE_RELEASE}/index.html"
)
BRIDGE_BUILDER_RELEASE = "0.1.0-qualification.12"
BRIDGE_BUILDER_URL = (
    "https://games.setnessconsulting.com/game-assets/bridge-builder/"
    f"{BRIDGE_BUILDER_RELEASE}/index.html"
)

PERSONA_FILES = {
    "first-time": LAB_ROOT / "personas" / "first-time-player.md",
    "normal": LAB_ROOT / "personas" / "normal-player.md",
    "expert": LAB_ROOT / "personas" / "expert-player.md",
    "adversarial": LAB_ROOT / "personas" / "adversarial-player.md",
}

MATH_DETECTIVE_PERSONA_FILES = {
    "first-time": LAB_ROOT / "personas" / "math-detective" / "first-time-player.md",
    "normal": LAB_ROOT / "personas" / "math-detective" / "normal-player.md",
    "expert": LAB_ROOT / "personas" / "math-detective" / "expert-player.md",
    "adversarial": LAB_ROOT / "personas" / "math-detective" / "adversarial-player.md",
}

BRIDGE_BUILDER_PERSONA_FILES = {
    "first-time": LAB_ROOT / "personas" / "bridge-builder" / "first-time-player.md",
    "normal": LAB_ROOT / "personas" / "bridge-builder" / "normal-player.md",
    "expert": LAB_ROOT / "personas" / "bridge-builder" / "expert-player.md",
    "adversarial": LAB_ROOT / "personas" / "bridge-builder" / "adversarial-player.md",
}

GAME_PROFILES: dict[str, dict[str, Any]] = {
    "number-line-jumper": {
        "name": "Number Line Jumper",
        "slug": "number-line-jumper",
        "revision": GAME_SHA,
        "revision_type": "source_git_sha",
        "source_sha": GAME_SHA,
        "url": "http://127.0.0.1:5173/",
        "personas": PERSONA_FILES,
        "rules": """\
This is a frozen Number Line Jumper browser game. Use only what is visible in
the current screenshot. The surface may begin at a level-selection screen and
may require visible buttons before gameplay. During a round, inspect the
number line, target, marker, prompts, and feedback before choosing the next
single action. Do not inspect source code, the DOM, network traffic, hidden
state, or browser accessibility metadata. Do not invent a defect from a
missing visual detail. This is a bounded exploratory playtest, not a speedrun.
""",
    },
    "math-detective": {
        "name": "Math Detective",
        "slug": "math-detective",
        "revision": MATH_DETECTIVE_RELEASE,
        "revision_type": "immutable_games_site_release",
        "source_sha": None,
        "url": MATH_DETECTIVE_URL,
        "personas": MATH_DETECTIVE_PERSONA_FILES,
        "rules": """\
This is the immutable Math Detective playtest-enhancements release. Use only
the game surface shown in the current screenshot. Read the visible case
briefing and clues, inspect evidence stations through their on-screen controls,
and use the displayed math and evidence to decide what happened. Distinguish
observed facts from guesses; do not invent evidence or a defect. Do not inspect
source code, the DOM, network traffic, hidden state, or browser metadata. This
is a bounded exploratory playtest, not a speedrun.
""",
    },
    "bridge-builder": {
        "name": "Bridge Builder",
        "slug": "bridge-builder",
        "revision": BRIDGE_BUILDER_RELEASE,
        "revision_type": "immutable_games_site_release",
        "source_sha": None,
        "url": BRIDGE_BUILDER_URL,
        "personas": BRIDGE_BUILDER_PERSONA_FILES,
        "rules": """\
This is the immutable Bridge Builder qualification release. Use only what is
visible on the game surface. For a comparable standard session, select Whole
planks and enable Relaxed build (no clock) at setup; leave the numeral display
at its default. Then start building, inspect the target gap and available
planks, and use the visible controls to fill the span exactly before checking
it. Observe the game's response and any next bridge. Do not inspect source code,
the DOM, network traffic, hidden state, or browser metadata. Do not invent a
defect from a missed click or an incorrect build. This is a bounded exploratory
playtest, not a speedrun.
""",
    },
}


# These are semantic controls, not provider-specific computer-use actions.
# Their bindings are consumed by the pinned GameWorld ActionExecutor after the
# OpenCode function call is mapped back into the low-level action shape.
ACTION_SPECS: list[dict[str, Any]] = [
    {
        "id": "click",
        "description": "Click a visible game-surface coordinate.",
        "binding": {"action": "click"},
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "Viewport x coordinate."},
                "y": {"type": "number", "description": "Viewport y coordinate."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "id": "scroll",
        "description": "Scroll the visible page by a small amount.",
        "binding": {"action": "scroll"},
        "parameters": {
            "type": "object",
            "properties": {
                "delta_x": {"type": "number", "description": "Horizontal scroll delta."},
                "delta_y": {"type": "number", "description": "Vertical scroll delta."},
            },
            "required": ["delta_x", "delta_y"],
        },
    },
    {
        "id": "press_left",
        "description": "Press the left arrow key once.",
        "binding": {"action": "press_key", "key": "ArrowLeft"},
    },
    {
        "id": "press_right",
        "description": "Press the right arrow key once.",
        "binding": {"action": "press_key", "key": "ArrowRight"},
    },
    {
        "id": "press_up",
        "description": "Press the up arrow key once.",
        "binding": {"action": "press_key", "key": "ArrowUp"},
    },
    {
        "id": "press_down",
        "description": "Press the down arrow key once.",
        "binding": {"action": "press_key", "key": "ArrowDown"},
    },
    {
        "id": "press_home",
        "description": "Press Home once when a visible game control indicates it.",
        "binding": {"action": "press_key", "key": "Home"},
    },
    {
        "id": "press_end",
        "description": "Press End once when a visible game control indicates it.",
        "binding": {"action": "press_key", "key": "End"},
    },
    {
        "id": "press_enter",
        "description": "Press Enter once when a visible control calls for it.",
        "binding": {"action": "press_key", "key": "Enter"},
    },
    {
        "id": "press_escape",
        "description": "Press Escape once when a visible control calls for it.",
        "binding": {"action": "press_key", "key": "Escape"},
    },
    {
        "id": "press_space",
        "description": "Press Space once when a visible control calls for it.",
        "binding": {"action": "press_key", "key": "Space"},
    },
    {
        "id": "wait",
        "description": "Wait briefly for a visible transition or animation.",
        "binding": {"action": "wait"},
        "parameters": {
            "type": "object",
            "properties": {
                "duration": {
                    "type": "number",
                    "description": "Seconds to wait, between 0 and 2.",
                }
            },
            "required": [],
        },
    },
    {
        "id": "done",
        "description": "End the bounded session after enough visible behavior has been exercised.",
        "binding": {"action": "wait", "duration": 0},
    },
]


def _load_gameworld(root: Path) -> None:
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)


def _read_api_key(api_key_file: str | None) -> str:
    if api_key_file:
        value = Path(api_key_file).expanduser().read_text(encoding="utf-8").strip()
    else:
        value = os.environ.get("OPENCODE_API_KEY", "").strip()
    if not value:
        raise RuntimeError(
            "OpenCode API key is empty. Pass --api-key-file or set OPENCODE_API_KEY."
        )
    return value


def _controls() -> SimpleNamespace:
    return SimpleNamespace(
        allowed_keys={
            "ArrowLeft",
            "ArrowRight",
            "ArrowUp",
            "ArrowDown",
            "Home",
            "End",
            "Enter",
            "Escape",
            "Space",
        },
        hold_duration=0.1,
        key_durations={},
        allow_clicks=True,
    )


def _semantic_controls() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            action_id=str(spec["id"]),
            description=str(spec.get("description", "")),
            binding=dict(spec.get("binding", {})),
            required=list(spec.get("parameters", {}).get("required", [])),
        )
        for spec in ACTION_SPECS
    ]


def _build_system_prompt(
    persona_text: str, max_steps: int, game_profile: str = "number-line-jumper"
) -> str:
    from agents.harness.prompting import render_semantic_action_space, render_system_prompt
    from opencode_agent import OUTPUT_FORMAT, PROMPT_TEMPLATE

    profile = GAME_PROFILES[game_profile]
    game_rules = str(profile["rules"])
    role_section = """\
You are the selected playtest persona. Choose exactly one registered semantic
control per step. Coordinates are viewport coordinates for the 1280x720 game
surface. Prefer visible buttons and deliberate keyboard actions. Use `done`
only after exercising enough of the visible flow or when the surface is
blocked. Keep reasoning short and tied to visible evidence.
"""
    task_prompt = f"""\
Play this frozen {profile['name']} build from the perspective described below
for at most {max_steps} model steps. Explore enough of the flow to reveal
concrete player-visible behavior. Call `done` when the bounded session has
sufficient evidence.

Persona:
{persona_text}
"""
    return render_system_prompt(
        template_name=PROMPT_TEMPLATE,
        game_rules=game_rules,
        task_prompt=task_prompt,
        role_section=role_section,
        computer_use_controls_section=None,
        semantic_action_space=render_semantic_action_space(_semantic_controls()),
        output_format=OUTPUT_FORMAT,
    )


async def _capture(manager: Any, destination: Path, name: str) -> Path:
    source = await manager.capture_screenshot(name)
    target = destination / name
    shutil.copy2(source, target)
    return target


async def _run(args: argparse.Namespace, api_key: str) -> int:
    profile = GAME_PROFILES[args.game_profile]
    game_url = args.game_url or str(profile["url"])
    persona_files = profile["personas"]
    gameworld_root = Path(args.gameworld_root).resolve()
    _load_gameworld(gameworld_root)

    from agents.harness.semantic_controls import inspect_semantic_controls_output
    from env.action_executor import ActionExecutor
    from env.browser_manager import BrowserConfig, BrowserGameManager
    from opencode_agent import (
        DEFAULT_ENDPOINT,
        DEFAULT_MODEL,
        DEFAULT_REASONING_EFFORT,
        DEFAULT_TOOL_CHOICE,
        OpenCodeGoAgent,
        OpenCodeGoConfig,
    )
    from playwright.async_api import async_playwright
    from utils import setup_logging

    setup_logging()

    if not DEFAULT_CHROME.is_file():
        raise RuntimeError(f"Windows Chrome executable not found: {DEFAULT_CHROME}")

    run_id = args.run_id or (
        f"gw-opencode-{args.persona}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    run_dir = Path(args.output_root).resolve() / run_id
    screenshots = run_dir / "screenshots"
    temp_screenshots = run_dir / "_tmp"
    screenshots.mkdir(parents=True, exist_ok=True)
    temp_screenshots.mkdir(parents=True, exist_ok=True)
    events_path = run_dir / "events.jsonl"

    persona_text = persona_files[args.persona].read_text(encoding="utf-8")
    session_id = f"gameworld-{args.persona}-{run_id}"
    config = OpenCodeGoConfig(
        model=args.model,
        api_key=api_key,
        endpoint=args.endpoint,
        protocol=args.protocol,
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
        tool_choice=args.tool_choice,
        request_timeout=args.timeout,
        session_id=session_id,
        system_prompt=_build_system_prompt(
            persona_text, args.max_steps, game_profile=args.game_profile
        ),
        enable_memory=False,
        log_session_id=session_id,
    )
    agent = OpenCodeGoAgent(config, semantic_controls_specs=ACTION_SPECS)

    browser_config = BrowserConfig(
        game_url=game_url,
        width=1280,
        height=720,
        headless=not args.headed,
        screenshot_dir=temp_screenshots,
        random_seed=42,
    )

    class WindowsChromeGameManager(BrowserGameManager):
        async def _launch_browser(self) -> None:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=self.config.headless,
                executable_path=str(DEFAULT_CHROME),
                args=self._browser_launch_args(),
            )
            self.context = await self.browser.new_context(
                viewport={"width": self.config.width, "height": self.config.height},
                service_workers="block",
            )
            self.page = await self.context.new_page()

    semantic_map = {
        str(spec["id"]): dict(spec.get("binding", {})) for spec in ACTION_SPECS
    }
    events: list[dict[str, Any]] = []
    provider_error = ""
    stop_reason = "max_steps"

    manager = WindowsChromeGameManager(browser_config)
    async with manager:
        page = manager.page
        if page is None:
            raise RuntimeError("GameWorld browser manager did not create a page")
        executor = ActionExecutor(page, controls=_controls())

        for step in range(1, args.max_steps + 1):
            before_text = (await page.locator("body").inner_text())[:4000]
            before_shot = await _capture(manager, screenshots, f"{step:02d}-before.png")
            event: dict[str, Any] = {
                "step": step,
                "before_text": before_text,
                "before_screenshot": str(before_shot),
                "provider": "opencode-go",
                "model": args.model,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            try:
                raw_action = await asyncio.to_thread(agent.get_action, before_shot)
                event["reasoning_metadata"] = agent.pop_reasoning_metadata()
                interaction = agent.pop_logged_interaction()
                event["raw_action"] = raw_action
                event["interaction"] = interaction
                inspected = inspect_semantic_controls_output(raw_action, semantic_map)
                event["semantic_inspection"] = inspected
                if not inspected["is_valid"]:
                    provider_error = str(inspected.get("reason", "invalid semantic action"))
                    event["ok"] = False
                    event["error"] = provider_error
                    events.append(event)
                    break

                control_id = inspected["control_id"]
                event["control_id"] = control_id
                if control_id == "done":
                    event["ok"] = True
                    event["stop"] = True
                    stop_reason = "model_done"
                    events.append(event)
                    break

                mapped_action = inspected["mapped_action"]
                executable = executor.inspect_action(mapped_action)
                event["executor_inspection"] = executable
                if not executable["is_valid"]:
                    provider_error = str(executable.get("reason", "invalid executable action"))
                    event["ok"] = False
                    event["error"] = provider_error
                    events.append(event)
                    break

                await executor.execute(mapped_action)
                await page.wait_for_timeout(300)
                event["ok"] = True
                event["mapped_action"] = mapped_action
                event["after_text"] = (await page.locator("body").inner_text())[:4000]
                after_shot = await _capture(manager, screenshots, f"{step:02d}-after.png")
                event["after_screenshot"] = str(after_shot)
                events.append(event)
            except Exception as exc:  # noqa: BLE001
                provider_error = str(exc)
                event["ok"] = False
                event["error"] = provider_error
                events.append(event)
                break

    status = "failed" if provider_error else "bounded_complete"
    manifest = {
        "run_id": run_id,
        "status": status,
        "framework": "gameworld",
        "framework_revision": GAMEWORLD_SHA,
        "game": profile["slug"],
        "game_revision": profile["revision"],
        "game_revision_type": profile["revision_type"],
        "game_source_sha": profile["source_sha"],
        "game_url": game_url,
        "persona": args.persona,
        "runner": "gameworld-native-contract-opencode",
        "provider": {
            "name": "opencode-go",
            "endpoint": args.endpoint,
            "model": args.model,
            "protocol": args.protocol,
            "reasoning_effort": args.reasoning_effort,
            "tool_choice": args.tool_choice,
            "output_token_limit": args.max_tokens,
            "credential_source": "runtime API-key file or OPENCODE_API_KEY environment variable",
            "credential_value_recorded": False,
        },
        "native_gameworld_agent": {
            "attempted": True,
            "adapter": "frameworks/gameworld/opencode_agent.py",
            "contract": "pinned GameWorld GeneralAgent semantic function-call contract",
            "upstream_checkout_modified": False,
        },
        "browser_deviation": {
            "documented_default": "Playwright-managed Chromium",
            "used": str(DEFAULT_CHROME),
            "reason": "GameWorld's pinned Python Playwright Chromium launch returned spawn UNKNOWN on Windows; system Chrome launched successfully.",
        },
        "max_steps": args.max_steps,
        "retry_context": (
            {
                "retry_of": args.retry_of,
                "reason": args.retry_reason,
            }
            if args.retry_of
            else None
        ),
        "stop_reason": stop_reason,
        "provider_error": provider_error,
        "events": events,
        "created_at": datetime.now(UTC).isoformat(),
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    with events_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

    print(
        json.dumps(
            {
                "run_id": run_id,
                "status": status,
                "run_dir": str(run_dir),
                "events": len(events),
                "stop_reason": stop_reason,
                "provider_error": provider_error,
            },
            indent=2,
        )
    )
    return 0 if not provider_error else 1


async def run(args: argparse.Namespace) -> int:
    api_key = _read_api_key(args.api_key_file)
    previous = os.environ.get("OPENCODE_API_KEY")
    os.environ["OPENCODE_API_KEY"] = api_key
    try:
        return await _run(args, api_key)
    finally:
        if previous is None:
            os.environ.pop("OPENCODE_API_KEY", None)
        else:
            os.environ["OPENCODE_API_KEY"] = previous


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game-profile",
        choices=sorted(GAME_PROFILES),
        default="number-line-jumper",
    )
    parser.add_argument("--persona", choices=sorted(PERSONA_FILES), required=True)
    parser.add_argument("--api-key-file")
    parser.add_argument("--gameworld-root", default=str(DEFAULT_GAMEWORLD_ROOT))
    parser.add_argument("--game-url")
    parser.add_argument("--run-id")
    parser.add_argument("--retry-of")
    parser.add_argument("--retry-reason")
    parser.add_argument("--output-root", default=str(LAB_ROOT / "runs" / "gameworld"))
    parser.add_argument("--model", default=os.environ.get("OPENCODE_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("OPENCODE_ENDPOINT", DEFAULT_ENDPOINT),
    )
    parser.add_argument(
        "--protocol",
        choices=("chat_completions", "responses"),
        default=os.environ.get("OPENCODE_PROTOCOL", DEFAULT_PROTOCOL),
    )
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument(
        "--reasoning-effort",
        default=os.environ.get("OPENCODE_REASONING_EFFORT", DEFAULT_REASONING_EFFORT),
    )
    parser.add_argument(
        "--tool-choice",
        default=os.environ.get("OPENCODE_TOOL_CHOICE", DEFAULT_TOOL_CHOICE),
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--headed", action="store_true")
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    raise SystemExit(asyncio.run(run(arguments)))

"""Bounded GameWorld browser run for the frozen Number Line Jumper build.

This is deliberately a lab-local controller. It reuses GameWorld's browser
manager and action executor, while Codex supplies a short persona action plan
and evidence review through the authenticated local CLI. The game remains
untouched and the run artifacts live under the ignored ``runs/`` tree.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any


LAB_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GAMEWORLD_ROOT = LAB_ROOT / ".frameworks" / "gameworld-upstream"
DEFAULT_CHROME = Path(os.environ.get("GAMEWORLD_CHROME_PATH", "C:/Program Files/Google/Chrome/Application/chrome.exe"))
GAME_SHA = "47a05480d7c32cee8f0991d6f6c0410be90d678e"
GAMEWORLD_SHA = "3c26bdab436800fd61ef40543b64ca40d12c7e4a"

PERSONA_FILES = {
    "first-time": LAB_ROOT / "personas" / "first-time-player.md",
    "normal": LAB_ROOT / "personas" / "normal-player.md",
    "expert": LAB_ROOT / "personas" / "expert-player.md",
    "adversarial": LAB_ROOT / "personas" / "adversarial-player.md",
}

DEFAULT_PLANS: dict[str, list[str]] = {
    "first-time": [
        "select_level_1_2",
        "start_guided",
        "keyboard_right",
        "land",
        "continue",
        "keyboard_left",
        "land",
        "exit",
    ],
    "normal": [
        "select_level_3_4",
        "start_guided",
        "keyboard_right",
        "land",
        "continue",
        "keyboard_left",
        "land",
        "continue",
        "keyboard_right",
        "land",
        "exit",
    ],
    "expert": [
        "select_level_5_6",
        "start_guided",
        "keyboard_home",
        "land",
        "continue",
        "keyboard_end",
        "land",
        "continue",
        "keyboard_right",
        "land",
        "exit",
    ],
    "adversarial": [
        "select_level_7_8",
        "start_guided",
        "rapid_keys",
        "duplicate_land",
        "duplicate_land",
        "continue",
        "exit",
    ],
}

ALLOWED_ACTIONS = sorted({action for plan in DEFAULT_PLANS.values() for action in plan})


def _load_gameworld(root: Path) -> None:
    sys.path.insert(0, str(root))


def _extract_agent_message(stdout: str) -> str:
    for line in reversed(stdout.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "item.completed":
            continue
        item = event.get("item") or {}
        if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
            return item["text"]
    return ""


def _parse_json_object(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    if cleaned.startswith("["):
        return None
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _ask_codex(prompt: str, screenshot: Path) -> tuple[dict[str, Any] | None, str, str]:
    if os.environ.get("GAMEWORLD_SKIP_CODEX") == "1":
        return None, "", "Codex invocation skipped by GAMEWORLD_SKIP_CODEX=1"

    codex = shutil.which("codex")
    if not codex:
        return None, "", "codex executable not found on PATH"

    command = [
        codex,
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--json",
        "-i",
        str(screenshot),
        "-",
    ]
    try:
        completed = subprocess.run(
            command,
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return None, "", f"Codex timed out after 180 seconds: {exc}"

    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    message = _extract_agent_message(stdout)
    parsed = _parse_json_object(message)
    error = ""
    if completed.returncode != 0:
        error = f"Codex exited {completed.returncode}: {stderr[-1000:]}"
    elif parsed is None:
        error = "Codex returned no parseable JSON object"
    return parsed, message, error


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


async def _click_locator(page: Any, executor: Any, locator: Any) -> None:
    await locator.wait_for(state="visible", timeout=4_000)
    await locator.scroll_into_view_if_needed()
    box = await locator.bounding_box()
    if not box:
        raise RuntimeError("visible locator has no bounding box")
    await executor.execute(
        {"action": "click", "x": box["x"] + box["width"] / 2, "y": box["y"] + box["height"] / 2}
    )


async def _run_action(page: Any, executor: Any, action: str) -> None:
    if action == "select_level_1_2":
        await _click_locator(page, executor, page.get_by_role("button", name=re.compile(r"Grades 1")))
    elif action == "select_level_3_4":
        await _click_locator(page, executor, page.get_by_role("button", name=re.compile(r"Grades 3")))
    elif action == "select_level_5_6":
        await _click_locator(page, executor, page.get_by_role("button", name=re.compile(r"Grades 5")))
    elif action == "select_level_7_8":
        await _click_locator(page, executor, page.get_by_role("button", name=re.compile(r"Grades 7")))
    elif action == "start_guided":
        await _click_locator(page, executor, page.get_by_role("button", name="Start guided round"))
    elif action in {"keyboard_left", "keyboard_right", "keyboard_home", "keyboard_end"}:
        key = {
            "keyboard_left": "ArrowLeft",
            "keyboard_right": "ArrowRight",
            "keyboard_home": "Home",
            "keyboard_end": "End",
        }[action]
        await executor.execute({"action": "press_key", "key": key})
    elif action == "rapid_keys":
        for key in ("ArrowRight", "ArrowLeft", "ArrowRight", "ArrowLeft"):
            await executor.execute({"action": "press_key", "key": key, "duration": 0.02})
    elif action in {"land", "duplicate_land"}:
        count = 2 if action == "duplicate_land" else 1
        for _ in range(count):
            await _click_locator(page, executor, page.get_by_role("button", name="Land here"))
    elif action == "continue":
        if await page.get_by_role("button", name="Continue").count():
            await _click_locator(page, executor, page.get_by_role("button", name="Continue"))
    elif action == "exit":
        if await page.get_by_role("button", name="Exit").count():
            await _click_locator(page, executor, page.get_by_role("button", name="Exit"))
    elif action == "wait":
        await executor.execute({"action": "wait", "duration": 0.5})
    else:
        raise ValueError(f"unsupported controller action: {action}")


async def _capture(manager: Any, destination: Path, name: str) -> Path:
    source = await manager.capture_screenshot(name)
    target = destination / name
    shutil.copy2(source, target)
    return target


async def run(args: argparse.Namespace) -> int:
    gameworld_root = Path(args.gameworld_root).resolve()
    _load_gameworld(gameworld_root)

    from env.action_executor import ActionExecutor
    from env.browser_manager import BrowserConfig, BrowserGameManager
    from playwright.async_api import async_playwright
    from utils import setup_logging

    # GameWorld installs its custom logger methods when ``utils`` is imported.
    # The normal ``play.py`` entry point does this before constructing the
    # browser manager; this lab-local runner must preserve that initialization.
    setup_logging()

    if not DEFAULT_CHROME.is_file():
        raise RuntimeError(f"Windows Chrome executable not found: {DEFAULT_CHROME}")

    run_id = args.run_id or f"gw-{args.persona}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    run_dir = Path(args.output_root).resolve() / run_id
    screenshots = run_dir / "screenshots"
    temp_screenshots = run_dir / "_tmp"
    screenshots.mkdir(parents=True, exist_ok=True)
    temp_screenshots.mkdir(parents=True, exist_ok=True)
    events_path = run_dir / "events.jsonl"

    persona_text = PERSONA_FILES[args.persona].read_text(encoding="utf-8")
    config = BrowserConfig(
        game_url=args.game_url,
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

    manager = WindowsChromeGameManager(config)
    events: list[dict[str, Any]] = []
    plan = list(DEFAULT_PLANS[args.persona])
    plan_message = ""
    plan_error = ""
    review: dict[str, Any] | None = None
    review_message = ""
    review_error = ""

    async with manager:
        page = manager.page
        if page is None:
            raise RuntimeError("GameWorld browser manager did not create a page")
        executor = ActionExecutor(page, controls=_controls())

        initial = await _capture(manager, screenshots, "00-initial.png")
        initial_text = (await page.locator("body").inner_text())[:5000]
        plan_prompt = f"""You are the Codex controller for one bounded GameWorld run.
Persona:
{persona_text}

The browser is the real frozen Number Line Jumper surface. Plan at most {args.max_actions} short UI actions.
Only use action IDs from this list: {', '.join(ALLOWED_ACTIONS)}.
Use the visible surface and persona perspective. Do not invent defects or use source code.
Return only JSON: {{\"actions\":[{{\"id\":\"action_id\",\"reason\":\"brief evidence-based reason\"}}],\"stop_reason\":\"...\"}}.

Visible text:
{initial_text}
"""
        planned, plan_message, plan_error = _ask_codex(plan_prompt, initial)
        if planned and isinstance(planned.get("actions"), list):
            candidate = [
                item.get("id")
                for item in planned["actions"]
                if isinstance(item, dict) and item.get("id") in ALLOWED_ACTIONS
            ]
            if candidate:
                plan = candidate[: args.max_actions]

        for step, action in enumerate(plan, start=1):
            before = (await page.locator("body").inner_text())[:3000]
            record: dict[str, Any] = {
                "step": step,
                "action": action,
                "before_text": before,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            try:
                await _run_action(page, executor, action)
                await page.wait_for_timeout(250)
                record["ok"] = True
            except Exception as exc:  # noqa: BLE001
                record["ok"] = False
                record["error"] = str(exc)
            record["after_text"] = (await page.locator("body").inner_text())[:3000]
            shot = await _capture(manager, screenshots, f"{step:02d}-{action}.png")
            record["screenshot"] = str(shot)
            events.append(record)
            if action == "exit" and record["ok"]:
                break

        final_shot = await _capture(manager, screenshots, "final.png")
        final_text = (await page.locator("body").inner_text())[:5000]
        review_prompt = f"""Review one completed GameWorld browser run for Number Line Jumper.
Persona: {args.persona}
Game SHA: {GAME_SHA}
GameWorld SHA: {GAMEWORLD_SHA}

Only report behavior supported by the attached final screenshot and the action evidence below.
Reject generic suggestions. Distinguish a confirmed game behavior from a controller/framework limitation or inconclusive result.
Return only JSON with keys: summary, completion, candidate_findings, rejected_generic_suggestions, limitations.
Each candidate finding must include title, observed_behavior, evidence_step, severity, confidence, recommended_improvement, expected_benefit, verification_approach.

Action evidence:
{json.dumps(events, indent=2, ensure_ascii=False)}

Final visible text:
{final_text}
"""
        review, review_message, review_error = _ask_codex(review_prompt, final_shot)

    manifest = {
        "run_id": run_id,
        "framework": "gameworld",
        "framework_revision": GAMEWORLD_SHA,
        "game": "number-line-jumper",
        "game_revision": GAME_SHA,
        "game_url": args.game_url,
        "persona": args.persona,
        "runner": "codex",
        "controller": "Codex CLI action-plan and evidence-review wrapper",
        "native_gameworld_agent": {
            "attempted": False,
            "reason": "GameWorld native provider clients require an unavailable provider API key or local model endpoint on this host.",
        },
        "browser_deviation": {
            "documented_default": "Playwright-managed Chromium",
            "used": str(DEFAULT_CHROME),
            "reason": "GameWorld's pinned Python Playwright Chromium launch returned spawn UNKNOWN on Windows; system Chrome launched successfully.",
        },
        "plan": plan,
        "plan_message": plan_message,
        "plan_error": plan_error,
        "events": events,
        "review": review,
        "review_message": review_message,
        "review_error": review_error,
        "created_at": datetime.now(UTC).isoformat(),
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with events_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "events": len(events), "plan": plan, "review_error": review_error}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persona", choices=sorted(PERSONA_FILES), required=True)
    parser.add_argument("--gameworld-root", default=str(DEFAULT_GAMEWORLD_ROOT))
    parser.add_argument("--game-url", default="http://127.0.0.1:5173/")
    parser.add_argument("--run-id")
    parser.add_argument("--output-root", default=str(LAB_ROOT / "runs" / "gameworld"))
    parser.add_argument("--max-actions", type=int, default=12)
    parser.add_argument("--headed", action="store_true")
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    raise SystemExit(asyncio.run(run(arguments)))

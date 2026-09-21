from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FRAMEWORKS = ("gameworld", "gamegen-verifier")
PERSONAS = ("first-time", "normal", "expert", "adversarial")
RUNNERS = ("codex", "opencode")
SEVERITIES = ("critical", "high", "medium", "low")
CONFIDENCES = ("high", "medium", "low")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

PERSONA_FILES = {
    "first-time": "first-time-player.md",
    "normal": "normal-player.md",
    "expert": "expert-player.md",
    "adversarial": "adversarial-player.md",
}

FINDING_REQUIRED = (
    "finding_id",
    "title",
    "framework",
    "persona",
    "category",
    "observed_behavior",
    "evidence",
    "severity",
    "confidence",
    "recommended_improvement",
    "expected_benefit",
    "verification_approach",
    "game_revision",
    "run_id",
)


class ContractError(ValueError):
    """Raised when experiment input violates the frozen contract."""


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError(f"expected JSON object in {path}")
    return data


def load_experiment(root: Path | None = None) -> dict[str, Any]:
    base = root or repo_root()
    data = load_json(base / "config" / "experiment.json")
    validate_experiment(data, base)
    return data["experiment"]


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def validate_experiment(data: dict[str, Any], root: Path) -> None:
    exp = data.get("experiment")
    if not isinstance(exp, dict):
        raise ContractError("config must contain an 'experiment' object")

    game = exp.get("game")
    if not isinstance(game, dict):
        raise ContractError("experiment.game must be an object")
    if game.get("id") != "number-line-jumper":
        raise ContractError("GAME-308 is locked to number-line-jumper")
    revision = _nonempty(game.get("revision"), "experiment.game.revision")
    if not SHA_RE.fullmatch(revision):
        raise ContractError("experiment.game.revision must be a 40-character lowercase git SHA")

    frameworks = exp.get("frameworks")
    if not isinstance(frameworks, dict) or set(frameworks) != set(FRAMEWORKS):
        raise ContractError(f"frameworks must be exactly {', '.join(FRAMEWORKS)}")
    for name in FRAMEWORKS:
        entry = frameworks[name]
        if not isinstance(entry, dict):
            raise ContractError(f"framework {name} must be an object")
        sha = _nonempty(entry.get("revision"), f"frameworks.{name}.revision")
        if not SHA_RE.fullmatch(sha):
            raise ContractError(f"frameworks.{name}.revision must be a 40-character lowercase git SHA")
        _nonempty(entry.get("repository"), f"frameworks.{name}.repository")

    personas = exp.get("personas")
    if personas != list(PERSONAS):
        raise ContractError(f"personas must be locked in order to {list(PERSONAS)}")
    for persona, filename in PERSONA_FILES.items():
        path = root / "personas" / filename
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise ContractError(f"missing or empty persona prompt for {persona}: {path}")

    runners = exp.get("runners")
    if not isinstance(runners, dict) or set(runners) != set(RUNNERS):
        raise ContractError(f"runners must be exactly {', '.join(RUNNERS)}")
    defaults = [name for name, cfg in runners.items() if isinstance(cfg, dict) and cfg.get("default") is True]
    if defaults != ["codex"]:
        raise ContractError("codex must be the single default runner")
    if "model_policy" not in runners["opencode"]:
        raise ContractError("opencode runner must document runtime model selection")


@dataclass(frozen=True)
class RunPlan:
    framework: str
    persona: str
    runner: str
    model: str | None
    game: str
    game_revision: str
    framework_revision: str
    game_url: str
    persona_prompt: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "framework": self.framework,
            "persona": self.persona,
            "runner": self.runner,
            "model": self.model,
            "game": self.game,
            "game_revision": self.game_revision,
            "framework_revision": self.framework_revision,
            "game_url": self.game_url,
            "persona_prompt": self.persona_prompt,
        }


def build_plan(
    framework: str,
    persona: str,
    runner: str = "codex",
    model: str | None = None,
    game_url: str | None = None,
    root: Path | None = None,
) -> RunPlan:
    if framework not in FRAMEWORKS:
        raise ContractError(f"unknown framework: {framework}")
    if persona not in PERSONAS:
        raise ContractError(f"unknown persona: {persona}")
    if runner not in RUNNERS:
        raise ContractError(f"unknown runner: {runner}")

    exp = load_experiment(root)
    prompt = f"personas/{PERSONA_FILES[persona]}"
    resolved_url = game_url or exp["game"]["runtime"]["default_url"]
    _nonempty(resolved_url, "game_url")

    clean_model = model.strip() if isinstance(model, str) and model.strip() else None
    return RunPlan(
        framework=framework,
        persona=persona,
        runner=runner,
        model=clean_model,
        game=exp["game"]["id"],
        game_revision=exp["game"]["revision"],
        framework_revision=exp["frameworks"][framework]["revision"],
        game_url=resolved_url,
        persona_prompt=prompt,
    )


def validate_finding(data: dict[str, Any]) -> None:
    missing = [field for field in FINDING_REQUIRED if field not in data]
    if missing:
        raise ContractError(f"finding missing required fields: {', '.join(missing)}")

    for field in (
        "finding_id",
        "title",
        "category",
        "observed_behavior",
        "recommended_improvement",
        "expected_benefit",
        "verification_approach",
        "run_id",
    ):
        _nonempty(data.get(field), field)

    if data["framework"] not in FRAMEWORKS:
        raise ContractError(f"framework must be one of {FRAMEWORKS}")
    if data["persona"] not in PERSONAS:
        raise ContractError(f"persona must be one of {PERSONAS}")
    if data["severity"] not in SEVERITIES:
        raise ContractError(f"severity must be one of {SEVERITIES}")
    if data["confidence"] not in CONFIDENCES:
        raise ContractError(f"confidence must be one of {CONFIDENCES}")

    revision = _nonempty(data.get("game_revision"), "game_revision")
    if not SHA_RE.fullmatch(revision):
        raise ContractError("game_revision must be a 40-character lowercase git SHA")

    evidence = data.get("evidence")
    if not isinstance(evidence, dict):
        raise ContractError("evidence must be an object")
    _nonempty(evidence.get("artifact_ref"), "evidence.artifact_ref")
    _nonempty(evidence.get("summary"), "evidence.summary")


def validate_finding_file(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_finding(data)
    return data

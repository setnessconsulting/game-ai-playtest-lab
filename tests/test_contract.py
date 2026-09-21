from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from playtest_lab.core import (
    ContractError,
    build_plan,
    load_experiment,
    repo_root,
    validate_finding,
    validate_finding_file,
)


class ExperimentContractTests(unittest.TestCase):
    def test_frozen_experiment_loads(self) -> None:
        exp = load_experiment()
        self.assertEqual(exp["game"]["id"], "number-line-jumper")
        self.assertEqual(
            exp["game"]["revision"],
            "47a05480d7c32cee8f0991d6f6c0410be90d678e",
        )
        self.assertTrue(exp["runners"]["codex"]["default"])
        self.assertFalse(exp["runners"]["opencode"]["default"])

    def test_default_plan_uses_codex_and_pinned_revisions(self) -> None:
        plan = build_plan("gameworld", "first-time")
        self.assertEqual(plan.runner, "codex")
        self.assertIsNone(plan.model)
        self.assertEqual(plan.game, "number-line-jumper")
        self.assertEqual(plan.game_url, "http://127.0.0.1:5173/")
        self.assertEqual(plan.persona_prompt, "personas/first-time-player.md")
        self.assertEqual(
            plan.framework_revision,
            "3c26bdab436800fd61ef40543b64ca40d12c7e4a",
        )

    def test_opencode_model_is_runtime_only(self) -> None:
        plan = build_plan(
            "gamegen-verifier",
            "adversarial",
            runner="opencode",
            model="provider/example-model",
        )
        self.assertEqual(plan.runner, "opencode")
        self.assertEqual(plan.model, "provider/example-model")
        frozen = json.loads((repo_root() / "config" / "experiment.json").read_text())
        self.assertNotIn("model", frozen["experiment"]["runners"]["opencode"])

    def test_unknown_values_are_rejected(self) -> None:
        with self.assertRaises(ContractError):
            build_plan("third-framework", "normal")
        with self.assertRaises(ContractError):
            build_plan("gameworld", "fifth-persona")
        with self.assertRaises(ContractError):
            build_plan("gameworld", "normal", runner="other")

    def test_sample_finding_is_valid(self) -> None:
        validate_finding_file(repo_root() / "reports" / "examples" / "sample-finding.json")

    def test_missing_evidence_is_rejected(self) -> None:
        sample = json.loads(
            (repo_root() / "reports" / "examples" / "sample-finding.json").read_text()
        )
        sample["evidence"] = {"artifact_ref": ""}
        with self.assertRaises(ContractError):
            validate_finding(sample)

    def test_invalid_sha_is_rejected(self) -> None:
        sample = json.loads(
            (repo_root() / "reports" / "examples" / "sample-finding.json").read_text()
        )
        sample["game_revision"] = "main"
        with self.assertRaises(ContractError):
            validate_finding(sample)

    def test_finding_file_requires_json_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ContractError):
                validate_finding_file(path)


if __name__ == "__main__":
    unittest.main()

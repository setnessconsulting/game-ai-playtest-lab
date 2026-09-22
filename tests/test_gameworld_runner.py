from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


RUNNER_PATH = Path(__file__).resolve().parents[1] / "frameworks" / "gameworld" / "number_line_jumper_runner.py"
SPEC = importlib.util.spec_from_file_location("number_line_jumper_runner", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class GameWorldRunnerTests(unittest.TestCase):
    def test_default_persona_plans_use_only_allowed_actions(self) -> None:
        for persona, plan in runner.DEFAULT_PLANS.items():
            with self.subTest(persona=persona):
                self.assertTrue(plan)
                self.assertTrue(set(plan).issubset(runner.ALLOWED_ACTIONS))

    def test_json_object_parser_accepts_fenced_agent_output(self) -> None:
        parsed = runner._parse_json_object('```json\n{"actions": []}\n```')
        self.assertEqual(parsed, {"actions": []})

    def test_json_object_parser_rejects_non_object_output(self) -> None:
        self.assertIsNone(runner._parse_json_object('[{"actions": []}]'))

    def test_codex_skip_is_explicit_and_noninteractive(self) -> None:
        with patch.dict(os.environ, {"GAMEWORLD_SKIP_CODEX": "1"}, clear=False):
            parsed, message, error = runner._ask_codex("prompt", RUNNER_PATH)
        self.assertIsNone(parsed)
        self.assertEqual(message, "")
        self.assertIn("GAMEWORLD_SKIP_CODEX", error)


if __name__ == "__main__":
    unittest.main()

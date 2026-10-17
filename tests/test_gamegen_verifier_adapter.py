from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "frameworks" / "gamegen-verifier"
GAME_DIR = ADAPTER / "workspace" / "games" / "number_line_jumper"
KEYPOINTS = GAME_DIR / "keypoints.md"
DESCRIPTION = ADAPTER / "workspace" / "descriptions_example" / "number_line_jumper.md"
CAMPAIGN = ADAPTER / "run_keypoint_campaign.py"

# Same heading and block grammar the pinned harness parses.
HEADING_RE = re.compile(r"^## Keypoint (\d+): \[(.+?)\] (.+)$", re.M)
BLOCK_LABELS = (
    "Precondition Game State Description",
    "Instruction Description",
    "Expected Result Description",
)


def experiment() -> dict:
    return json.loads((ROOT / "config" / "experiment.json").read_text(encoding="utf-8"))["experiment"]


def parse_keypoints(text: str) -> list[dict[str, str]]:
    matches = list(HEADING_RE.finditer(text))
    items = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start():end]
        item = {"id": match.group(1), "category": match.group(2), "heading": match.group(3).strip()}
        for label in BLOCK_LABELS:
            found = re.search(rf"\*\*{re.escape(label)}:\*\*\n(.+?)(?:\n\n|\Z)", block, re.S)
            item[label] = " ".join(found.group(1).split()) if found else ""
        items.append(item)
    return items


def load_campaign_module():
    spec = importlib.util.spec_from_file_location("ggv_run_keypoint_campaign", CAMPAIGN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GameGenVerifierAdapterTests(unittest.TestCase):
    def test_adapter_files_exist(self) -> None:
        for path in (
            KEYPOINTS,
            DESCRIPTION,
            GAME_DIR / "package.json",
            GAME_DIR / "dev-server.mjs",
            GAME_DIR / "data.md",
            GAME_DIR / "state_injection_api.md",
        ):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), f"missing adapter file: {path}")

    def test_description_and_game_stay_on_the_frozen_revision(self) -> None:
        contract = experiment()
        frozen = contract["game"]["revision"]
        text = DESCRIPTION.read_text(encoding="utf-8")
        self.assertIn(frozen, text)
        self.assertIn(contract["game"]["repository"], text)

    def test_five_locked_keypoints_parse_with_the_harness_grammar(self) -> None:
        items = parse_keypoints(KEYPOINTS.read_text(encoding="utf-8"))
        self.assertEqual(len(items), 5)
        self.assertEqual([item["id"] for item in items], ["1", "2", "3", "4", "5"])
        for item in items:
            with self.subTest(keypoint=item["id"]):
                self.assertTrue(item["category"].strip())
                self.assertTrue(item["heading"])
                for label in BLOCK_LABELS:
                    self.assertTrue(item[label].strip(), f"keypoint {item['id']} missing {label}")

    def test_keypoints_cover_the_great_five_behaviours(self) -> None:
        items = parse_keypoints(KEYPOINTS.read_text(encoding="utf-8"))
        joined = {item["id"]: (item["heading"] + " " + item["Instruction Description"]).lower() for item in items}
        self.assertIn("first-time player", items[0]["heading"].lower())
        self.assertIn("pointer", joined["2"])
        self.assertIn("feedback", joined["3"])
        self.assertIn("progress", joined["4"])
        self.assertIn("reload", joined["5"])

    def test_state_injection_gap_is_documented_not_faked(self) -> None:
        injection = (GAME_DIR / "state_injection_api.md").read_text(encoding="utf-8")
        data = (GAME_DIR / "data.md").read_text(encoding="utf-8")
        self.assertIn("no state injection API exists", injection)
        self.assertIn("window.getGameState()", injection)
        self.assertIn("window.injectGameState", data)
        self.assertIn("no test hook", data)

    def test_dev_shim_serves_the_frozen_checkout_and_writes_nothing(self) -> None:
        shim = (GAME_DIR / "dev-server.mjs").read_text(encoding="utf-8")
        self.assertIn("NLJ_FROZEN_ROOT", shim)
        self.assertIn("frozen-root.json", shim)
        self.assertIn('"run", "dev"', shim)
        self.assertNotIn("writeFile", shim)
        self.assertNotIn("mkdir", shim)

    def test_prepare_fails_closed_on_the_pinned_revisions(self) -> None:
        prepare = (ADAPTER / "prepare_workspace.py").read_text(encoding="utf-8")
        self.assertIn("config", prepare)
        self.assertIn("experiment.json", prepare)
        self.assertIn("revision mismatch", prepare)
        self.assertIn("git_revision", prepare)
        self.assertIn("status\", \"--porcelain", prepare)

    def test_campaign_command_uses_the_documented_resume_path(self) -> None:
        module = load_campaign_module()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            run_dir = workspace / "runs" / module.GAME_NAME / "unit-test-run"
            run_dir.mkdir(parents=True)
            (run_dir / "keypoints.snapshot.md").write_text("# stub\n", encoding="utf-8")
            pyshim = workspace / "pyshim"
            pyshim.mkdir()
            for name in ("python3", "python3.exe"):
                (pyshim / name).write_text("", encoding="utf-8")
            codex_dir = workspace / "codex-bin"
            codex_dir.mkdir()
            (codex_dir / "codex").write_text("", encoding="utf-8")
            buffer = StringIO()
            argv = [
                "run_keypoint_campaign.py",
                "--workspace",
                str(workspace),
                "--run-id",
                "unit-test-run",
                "--python3-bin",
                str(pyshim),
                "--codex-bin",
                str(codex_dir),
                "--plan-only",
            ]
            import sys

            previous = sys.argv
            sys.argv = argv
            try:
                with redirect_stdout(buffer):
                    code = module.main()
            finally:
                sys.argv = previous
            self.assertEqual(code, 0)
            record = json.loads(buffer.getvalue())
            command = record["command"]
            self.assertIn("--resume-run", command)
            self.assertIn("--min-keypoints", command)
            self.assertIn("5", command)
            self.assertIn(module.GAME_NAME, command)
            self.assertIn("codex", command)
            self.assertTrue(str(record["cwd"]).endswith("gamegen-verifier"))
            self.assertEqual([Path(item) for item in record["path_prepended"]], [pyshim.resolve(), codex_dir.resolve()])


if __name__ == "__main__":
    unittest.main()

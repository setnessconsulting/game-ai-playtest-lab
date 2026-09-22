from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


LAB_ROOT = Path(__file__).resolve().parents[1]
GAMEWORLD_ROOT = LAB_ROOT / ".frameworks" / "gameworld-upstream"
ADAPTER_PATH = LAB_ROOT / "frameworks" / "gameworld" / "opencode_agent.py"
RUNNER_PATH = LAB_ROOT / "frameworks" / "gameworld" / "opencode_number_line_jumper_runner.py"

if str(GAMEWORLD_ROOT) not in sys.path:
    sys.path.insert(0, str(GAMEWORLD_ROOT))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load_module("gameworld_opencode_agent_test", ADAPTER_PATH)
runner = _load_module("gameworld_opencode_runner_test", RUNNER_PATH)


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class GameWorldOpenCodeTests(unittest.TestCase):
    def test_payload_uses_chat_tools_and_image_placeholder_for_logs(self) -> None:
        config = adapter.OpenCodeGoConfig(
            model="test-model",
            api_key="test-key",
            endpoint="https://example.invalid/chat/completions",
            enable_memory=False,
            session_id="test-session",
        )
        agent = adapter.OpenCodeGoAgent(
            config,
            semantic_controls_specs=[
                {
                    "id": "press_left",
                    "description": "Press left.",
                    "binding": {"action": "press_key", "key": "ArrowLeft"},
                }
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            screenshot = Path(temp_dir) / "screen.png"
            screenshot.write_bytes(b"fake-png-bytes")
            payload = agent.build_request_payload(
                system_prompt="system",
                user_prompt="Game screen:",
                memory_entries=[],
                tools=agent.build_tools(),
                screenshot_path=screenshot,
            )

        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["reasoning_effort"], "max")
        self.assertEqual(payload["tool_choice"], "auto")
        self.assertEqual(payload["max_tokens"], 8192)
        self.assertEqual(payload["tools"][0]["type"], "function")
        self.assertEqual(payload["tools"][0]["function"]["name"], "press_left")
        image_url = payload["messages"][1]["content"][-1]["image_url"]["url"]
        self.assertTrue(image_url.startswith("data:image/png;base64,"))

        response = _FakeResponse({"output": []})
        with patch.object(adapter.requests, "post", return_value=response) as post:
            agent.send_request(payload)

        self.assertEqual(
            post.call_args.args[0], "https://example.invalid/chat/completions"
        )
        headers = post.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertEqual(headers["x-opencode-session"], "test-session")
        self.assertNotIn("test-key", json.dumps(payload))

    def test_extracts_chat_completions_function_call(self) -> None:
        response = _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "reasoning_content": "Visible target.",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "press_left",
                                        "arguments": json.dumps(
                                            {"reasoning": "Move toward the visible target."}
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        )
        config = adapter.OpenCodeGoConfig(
            api_key="test-key",
            endpoint="https://example.invalid/chat/completions",
            enable_memory=False,
        )
        agent = adapter.OpenCodeGoAgent(config)
        self.assertEqual(
            agent.extract_tool_call(response),
            {
                "tool_name": "press_left",
                "arguments": {"reasoning": "Move toward the visible target."},
                "tool_call_id": "call-1",
            },
        )
        self.assertEqual(agent.extract_reasoning(response), "Visible target.")
        self.assertEqual(
            agent.pop_reasoning_metadata(), {"present": True, "characters": 15}
        )

    def test_missing_function_call_is_not_converted_to_an_action(self) -> None:
        response = _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Click the target.",
                        }
                    }
                ]
            }
        )
        config = adapter.OpenCodeGoConfig(
            api_key="test-key",
            endpoint="https://example.invalid/chat/completions",
            enable_memory=False,
        )
        agent = adapter.OpenCodeGoAgent(config)
        self.assertIsNone(agent.extract_tool_call(response))

    def test_reasoning_is_redacted_from_logged_response(self) -> None:
        response = _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "reasoning_content": "secret hidden chain",
                            "tool_calls": [],
                        }
                    }
                ]
            }
        )
        serialized = adapter.OpenCodeGoAgent._stringify_raw_response(response)
        self.assertNotIn("secret hidden chain", serialized)
        self.assertIn("<redacted_reasoning>", serialized)

    def test_key_file_loader_returns_value_without_printing_or_requiring_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            key_file = Path(temp_dir) / "opencode-key.txt"
            key_file.write_text("test-key\n", encoding="utf-8")
            self.assertEqual(runner._read_api_key(str(key_file)), "test-key")


if __name__ == "__main__":
    unittest.main()

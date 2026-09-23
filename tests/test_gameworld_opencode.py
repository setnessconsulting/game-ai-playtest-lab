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

    def test_responses_payload_uses_flat_tools_and_multimodal_input(self) -> None:
        config = adapter.OpenCodeGoConfig(
            model="muse-spark-1.3-contributor",
            api_key="test-key",
            endpoint="https://example.invalid/responses",
            protocol="responses",
            reasoning_effort="xhigh",
            enable_memory=False,
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

        self.assertEqual(payload["model"], "muse-spark-1.3-contributor")
        self.assertEqual(payload["reasoning"], {"effort": "xhigh"})
        self.assertEqual(payload["tool_choice"], "auto")
        self.assertEqual(payload["max_output_tokens"], 8192)
        self.assertFalse(payload["store"])
        self.assertEqual(payload["tools"][0]["type"], "function")
        self.assertEqual(payload["tools"][0]["name"], "press_left")
        self.assertEqual(payload["tools"][0]["parameters"]["required"], ["reasoning"])
        self.assertNotIn("function", payload["tools"][0])
        self.assertEqual(payload["input"][0]["role"], "system")
        self.assertEqual(payload["input"][1]["content"][0]["type"], "input_text")
        image = payload["input"][1]["content"][-1]
        self.assertEqual(image["type"], "input_image")
        self.assertTrue(image["image_url"].startswith("data:image/png;base64,"))

    def test_responses_tools_mark_all_properties_required_for_strict_schema(self) -> None:
        config = adapter.OpenCodeGoConfig(
            api_key="test-key",
            endpoint="https://example.invalid/responses",
            protocol="responses",
            enable_memory=False,
        )
        agent = adapter.OpenCodeGoAgent(
            config,
            semantic_controls_specs=[
                {
                    "id": "wait",
                    "description": "Wait briefly.",
                    "binding": {"action": "wait"},
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "duration": {"type": "number"},
                        },
                        "required": [],
                    },
                }
            ],
        )
        tool = agent.build_tools()[0]
        self.assertEqual(
            tool["parameters"]["required"], ["duration", "reasoning"]
        )

    def test_provider_error_is_diagnostic_but_never_echoes_api_key(self) -> None:
        response = _FakeResponse(
            {"error": {"message": "Missing required duration", "param": "parameters"}}
        )
        response.status_code = 400

        def raise_bad_request() -> None:
            raise adapter.requests.HTTPError("bad request")

        response.raise_for_status = raise_bad_request
        config = adapter.OpenCodeGoConfig(
            api_key="secret-key-value",
            endpoint="https://example.invalid/responses",
            protocol="responses",
            enable_memory=False,
        )
        agent = adapter.OpenCodeGoAgent(config)
        with patch.object(adapter.requests, "post", return_value=response):
            with self.assertRaises(RuntimeError) as raised:
                agent.send_request({})
        self.assertIn("Missing required duration", str(raised.exception))
        self.assertNotIn("secret-key-value", str(raised.exception))

    def test_extracts_responses_function_call_and_redacts_reasoning_item(self) -> None:
        response = _FakeResponse(
            {
                "output": [
                    {
                        "type": "reasoning",
                        "summary": [{"type": "summary_text", "text": "private thought"}],
                        "encrypted_content": "opaque-reasoning-payload",
                    },
                    {
                        "type": "function_call",
                        "call_id": "call-2",
                        "name": "press_left",
                        "arguments": json.dumps(
                            {"reasoning": "Move toward the visible target."}
                        ),
                    },
                ]
            }
        )
        config = adapter.OpenCodeGoConfig(
            api_key="test-key",
            endpoint="https://example.invalid/responses",
            protocol="responses",
            enable_memory=False,
        )
        agent = adapter.OpenCodeGoAgent(config)

        self.assertEqual(
            agent.extract_tool_call(response),
            {
                "tool_name": "press_left",
                "arguments": {"reasoning": "Move toward the visible target."},
            },
        )
        self.assertIsNone(agent.extract_reasoning(response))
        self.assertEqual(
            agent.pop_reasoning_metadata(),
            {
                "present": True,
                "characters": len("private thought")
                + len("opaque-reasoning-payload"),
            },
        )
        serialized = adapter.OpenCodeGoAgent._stringify_raw_response(response)
        self.assertNotIn("private thought", serialized)
        self.assertNotIn("opaque-reasoning-payload", serialized)
        self.assertIn("<redacted_reasoning>", serialized)

    def test_response_log_records_http_status(self) -> None:
        response = _FakeResponse({"status": "completed", "output": []})
        response.status_code = 200
        serialized = adapter.OpenCodeGoAgent._stringify_raw_response(response)
        self.assertEqual(json.loads(serialized)["transport_http_status"], 200)

    def test_responses_plain_text_does_not_become_an_action(self) -> None:
        response = _FakeResponse(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "Click the target."}],
                    }
                ]
            }
        )
        config = adapter.OpenCodeGoConfig(
            api_key="test-key",
            endpoint="https://example.invalid/responses",
            protocol="responses",
            enable_memory=False,
        )
        agent = adapter.OpenCodeGoAgent(config)
        self.assertIsNone(agent.extract_tool_call(response))

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

    def test_math_detective_profile_pins_release_and_uses_game_specific_prompt(self) -> None:
        profile = runner.GAME_PROFILES["math-detective"]
        self.assertEqual(profile["slug"], "math-detective")
        self.assertEqual(
            profile["revision"], "2026.09.21-playtest-enhancements.1"
        )
        self.assertEqual(profile["revision_type"], "immutable_games_site_release")
        self.assertIsNone(profile["source_sha"])
        self.assertEqual(
            profile["url"],
            "https://games.setnessconsulting.com/game-assets/math-detective/"
            "2026.09.21-playtest-enhancements.1/index.html",
        )
        self.assertEqual(set(profile["personas"]), set(runner.PERSONA_FILES))

        with patch.dict(sys.modules, {"opencode_agent": adapter}):
            prompt = runner._build_system_prompt(
                "First-time persona", 8, game_profile="math-detective"
            )
        self.assertIn("Math Detective", prompt)
        self.assertIn("case", prompt)
        self.assertIn("evidence stations", prompt)
        self.assertNotIn("Number Line Jumper", prompt)

    def test_bridge_builder_profile_pins_release_and_uses_game_specific_prompt(self) -> None:
        profile = runner.GAME_PROFILES["bridge-builder"]
        self.assertEqual(profile["slug"], "bridge-builder")
        self.assertEqual(profile["revision"], "0.1.0-qualification.12")
        self.assertEqual(profile["revision_type"], "immutable_games_site_release")
        self.assertIsNone(profile["source_sha"])
        self.assertEqual(
            profile["url"],
            "https://games.setnessconsulting.com/game-assets/bridge-builder/"
            "0.1.0-qualification.12/index.html",
        )
        self.assertEqual(set(profile["personas"]), set(runner.PERSONA_FILES))

        with patch.dict(sys.modules, {"opencode_agent": adapter}):
            prompt = runner._build_system_prompt(
                "First-time persona", 8, game_profile="bridge-builder"
            )
        self.assertIn("Whole", prompt)
        self.assertIn("Relaxed build", prompt)
        self.assertIn("fill the span exactly", prompt)
        self.assertNotIn("Math Detective", prompt)
        self.assertNotIn("Number Line Jumper", prompt)


if __name__ == "__main__":
    unittest.main()

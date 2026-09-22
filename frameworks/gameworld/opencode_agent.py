"""Lab-local OpenCode Go adapter for the pinned GameWorld general-agent flow.

The adapter deliberately lives outside the pinned GameWorld checkout. It
implements the same ``GeneralAgent`` contract as the upstream model adapters,
but sends an OpenAI-compatible Chat Completions request to OpenCode Go so the
lab can select DeepSeek without changing the frozen framework source.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from agents.harness.function_calling_utils import build_openai_action_tools
from agents.mm_agents.base.base_client import BaseClientConfig
from agents.mm_agents.base.general_agent import GeneralAgent


DEFAULT_ENDPOINT = "https://opencode.ai/zen/go/v1/chat/completions"
DEFAULT_MODEL = "deepseek-v4.1-flash"
DEFAULT_REASONING_EFFORT = "max"
DEFAULT_TOOL_CHOICE = "auto"


@dataclass
class OpenCodeGoConfig(BaseClientConfig):
    """Runtime settings for an OpenCode Go Chat Completions client."""

    model: str = field(
        default_factory=lambda: os.environ.get("OPENCODE_MODEL", DEFAULT_MODEL)
    )
    model_type: str = "general"
    api_key: str | None = field(
        default_factory=lambda: os.environ.get("OPENCODE_API_KEY")
    )
    endpoint: str = field(
        default_factory=lambda: os.environ.get("OPENCODE_ENDPOINT", DEFAULT_ENDPOINT)
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.environ.get("OPENCODE_MAX_TOKENS", "8192"))
    )
    reasoning_effort: str = field(
        default_factory=lambda: os.environ.get(
            "OPENCODE_REASONING_EFFORT", DEFAULT_REASONING_EFFORT
        )
    )
    tool_choice: str = field(
        default_factory=lambda: os.environ.get(
            "OPENCODE_TOOL_CHOICE", DEFAULT_TOOL_CHOICE
        )
    )
    request_timeout: float = field(
        default_factory=lambda: float(os.environ.get("OPENCODE_TIMEOUT_SECONDS", "120"))
    )
    session_id: str | None = field(
        default_factory=lambda: os.environ.get("OPENCODE_SESSION_ID")
    )


class OpenCodeGoAgent(GeneralAgent):
    """GameWorld semantic-control agent backed by OpenCode Go DeepSeek."""

    def __init__(self, config: OpenCodeGoConfig, **shared_tools: Any) -> None:
        super().__init__(config, **shared_tools)
        self._api_key = self._resolve_api_key(
            config.api_key,
            env_vars=("OPENCODE_API_KEY",),
        )
        self._endpoint = self._require_endpoint(config.endpoint, "OpenCode Go")
        self._session_id = (
            config.session_id
            or config.log_session_id
            or f"gameworld-opencode-{uuid.uuid4().hex}"
        )
        self._last_reasoning: str | None = None

    def build_tools(self) -> list[dict[str, object]]:
        """Build strict Chat Completions function tools from GameWorld specs."""

        source_tools = build_openai_action_tools(self._semantic_controls_specs)
        chat_tools: list[dict[str, object]] = []
        for tool in source_tools:
            function = {
                key: tool[key]
                for key in ("name", "description", "parameters", "strict")
                if key in tool
            }
            chat_tools.append({"type": "function", "function": function})
        return chat_tools

    def build_request_payload(
        self,
        *,
        system_prompt: str | None,
        user_prompt: str,
        memory_entries: list[object],
        tools: list[dict[str, object]],
        screenshot_path: Path,
    ) -> dict[str, object]:
        message_content = self._build_user_content(
            memory_entries=memory_entries,
            append_user_text=lambda text: {"type": "text", "text": text},
            append_user_image=lambda image_file: {
                "type": "image_url",
                "image_url": {
                    "url": self._build_data_url(image_file),
                    "detail": "high",
                },
            },
            user_prompt=user_prompt,
            screenshot_path=screenshot_path,
        )
        payload: dict[str, object] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": message_content},
            ],
            "max_tokens": self.config.max_tokens,
            "reasoning_effort": self.config.reasoning_effort,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = self.config.tool_choice
        return payload

    def send_request(self, request_payload: dict[str, object]) -> requests.Response:
        """Send one request without exposing the credential to logs or artifacts."""

        response = requests.post(
            self._endpoint,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "game-ai-playtest-lab/1.0",
                "x-opencode-session": self._session_id,
            },
            json=request_payload,
            timeout=self.config.request_timeout,
        )
        response.raise_for_status()
        return response

    @staticmethod
    def _response_message(response: requests.Response) -> dict[str, object] | None:
        payload = response.json()
        choices = payload.get("choices") if isinstance(payload, dict) else None
        if not isinstance(choices, list) or not choices:
            return None
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return None
        message = first_choice.get("message")
        return message if isinstance(message, dict) else None

    def extract_tool_call(self, response: requests.Response) -> dict[str, object] | None:
        """Extract one Chat Completions function call into GameWorld shape."""

        message = self._response_message(response)
        if message is None:
            return None
        return self._extract_tool_call_from_message(message)

    def extract_reasoning(self, response: requests.Response) -> str | None:
        """Capture provider reasoning for local metadata without persisting it."""

        message = self._response_message(response)
        reasoning = self._extract_reasoning_content(message)
        self._last_reasoning = reasoning
        return reasoning

    def pop_reasoning_metadata(self) -> dict[str, object]:
        """Return safe reasoning metadata without returning hidden reasoning text."""

        reasoning = self._last_reasoning
        self._last_reasoning = None
        return {
            "present": bool(reasoning),
            "characters": len(reasoning or ""),
        }

    @staticmethod
    def _stringify_raw_response(response: requests.Response) -> str:
        """Store safe provider metadata without serializing hidden reasoning."""

        try:
            payload = response.json()
            return json.dumps(
                OpenCodeGoAgent._redact_reasoning(payload),
                ensure_ascii=False,
                default=str,
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            # Do not preserve an unparseable body: it could contain provider
            # thinking text that cannot be safely field-redacted.
            return "<unparseable_provider_response_redacted>"

    @classmethod
    def _redact_reasoning(cls, value: object) -> object:
        if isinstance(value, dict):
            return {
                key: "<redacted_reasoning>"
                if key.lower() in {"reasoning", "reasoning_content", "thinking"}
                else cls._redact_reasoning(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._redact_reasoning(item) for item in value]
        return value


Client = OpenCodeGoAgent
Config = OpenCodeGoConfig
PROMPT_TEMPLATE = "game_agent.j2"
OUTPUT_FORMAT = """\
- You must call exactly ONE tool per step.
- The tool name must be a registered action id.
- Include `reasoning` as a short rationale grounded in the visible screenshot.
- Do not output free-form text.
"""


__all__ = [
    "Client",
    "Config",
    "DEFAULT_MODEL",
    "DEFAULT_ENDPOINT",
    "DEFAULT_REASONING_EFFORT",
    "DEFAULT_TOOL_CHOICE",
    "OpenCodeGoAgent",
    "OpenCodeGoConfig",
    "OUTPUT_FORMAT",
    "PROMPT_TEMPLATE",
]

"""Lab-local OpenCode Go adapter for the pinned GameWorld general-agent flow.

The adapter deliberately lives outside the pinned GameWorld checkout. It
implements the same ``GeneralAgent`` contract as the upstream model adapters
and supports OpenCode Go's Chat Completions and Responses API model routes.
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
DEFAULT_PROTOCOL = "chat_completions"


@dataclass
class OpenCodeGoConfig(BaseClientConfig):
    """Runtime settings for an OpenCode Go client."""

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
    protocol: str = field(
        default_factory=lambda: os.environ.get("OPENCODE_PROTOCOL", DEFAULT_PROTOCOL)
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
    """GameWorld semantic-control agent backed by OpenCode Go."""

    def __init__(self, config: OpenCodeGoConfig, **shared_tools: Any) -> None:
        super().__init__(config, **shared_tools)
        self._api_key = self._resolve_api_key(
            config.api_key,
            env_vars=("OPENCODE_API_KEY",),
        )
        self._endpoint = self._require_endpoint(config.endpoint, "OpenCode Go")
        if config.protocol not in {"chat_completions", "responses"}:
            raise ValueError(f"Unsupported OpenCode protocol: {config.protocol}")
        self._session_id = (
            config.session_id
            or config.log_session_id
            or f"gameworld-opencode-{uuid.uuid4().hex}"
        )
        self._last_reasoning: str | None = None
        self._last_reasoning_characters = 0
        self._last_reasoning_present = False

    def build_tools(self) -> list[dict[str, object]]:
        """Build strict function tools in the selected protocol's schema."""

        source_tools = build_openai_action_tools(self._semantic_controls_specs)
        if self.config.protocol == "responses":
            responses_tools: list[dict[str, object]] = []
            for source_tool in source_tools:
                tool = dict(source_tool)
                parameters = tool.get("parameters")
                if isinstance(parameters, dict):
                    schema = dict(parameters)
                    properties = schema.get("properties")
                    if isinstance(properties, dict):
                        schema["required"] = list(properties)
                    tool["parameters"] = schema
                responses_tools.append(tool)
            return responses_tools

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
        if self.config.protocol == "responses":
            input_content = self._build_user_content(
                memory_entries=memory_entries,
                append_user_text=lambda text: {"type": "input_text", "text": text},
                append_user_image=lambda image_file: {
                    "type": "input_image",
                    "image_url": self._build_data_url(image_file),
                },
                user_prompt=user_prompt,
                screenshot_path=screenshot_path,
            )
            payload: dict[str, object] = {
                "model": self.config.model,
                "input": [
                    {
                        "role": "system",
                        "content": [
                            {"type": "input_text", "text": system_prompt or ""}
                        ],
                    },
                    {"role": "user", "content": input_content},
                ],
                "max_output_tokens": self.config.max_tokens,
                "reasoning": {"effort": self.config.reasoning_effort},
                "store": False,
            }
        else:
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
            payload = {
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
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                detail = json.dumps(
                    self._redact_reasoning(response.json()),
                    ensure_ascii=False,
                    default=str,
                )
            except (TypeError, ValueError, json.JSONDecodeError):
                detail = "<non-json provider error body redacted>"
            detail = detail.replace(self._api_key, "<redacted>")
            status_code = getattr(response, "status_code", "unknown")
            raise RuntimeError(
                f"OpenCode Go HTTP {status_code}: {detail[:2000]}"
            ) from exc
        return response

    @staticmethod
    def _response_payload(response: requests.Response) -> dict[str, object] | None:
        payload = response.json()
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _response_message(response: requests.Response) -> dict[str, object] | None:
        payload = OpenCodeGoAgent._response_payload(response)
        choices = payload.get("choices") if payload is not None else None
        if not isinstance(choices, list) or not choices:
            return None
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return None
        message = first_choice.get("message")
        return message if isinstance(message, dict) else None

    def extract_tool_call(self, response: requests.Response) -> dict[str, object] | None:
        """Extract one provider function call into GameWorld shape."""

        if self.config.protocol == "responses":
            payload = self._response_payload(response)
            output = payload.get("output") if payload is not None else None
            if not isinstance(output, list):
                return None
            return self._extract_tool_call_from_output_items(output)

        message = self._response_message(response)
        if message is None:
            return None
        return self._extract_tool_call_from_message(message)

    def extract_reasoning(self, response: requests.Response) -> str | None:
        """Capture safe reasoning metadata without persisting hidden reasoning."""

        if self.config.protocol == "responses":
            payload = self._response_payload(response)
            output = payload.get("output", []) if payload is not None else []
            reasoning_items = (
                [
                    item
                    for item in output
                    if isinstance(item, dict) and item.get("type") == "reasoning"
                ]
                if isinstance(output, list)
                else []
            )
            self._last_reasoning = None
            self._last_reasoning_present = bool(reasoning_items)
            self._last_reasoning_characters = sum(
                self._reasoning_character_count(item.get(key))
                for item in reasoning_items
                for key in ("summary", "encrypted_content")
                if item.get(key) is not None
            )
            return None

        message = self._response_message(response)
        reasoning = self._extract_reasoning_content(message)
        self._last_reasoning = reasoning
        self._last_reasoning_present = bool(reasoning)
        self._last_reasoning_characters = len(reasoning or "")
        return reasoning

    @classmethod
    def _reasoning_character_count(cls, value: object) -> int:
        if isinstance(value, str):
            return len(value)
        if isinstance(value, dict):
            return sum(
                cls._reasoning_character_count(item)
                for key, item in value.items()
                if key in {"text", "summary", "encrypted_content"}
            )
        if isinstance(value, list):
            return sum(cls._reasoning_character_count(item) for item in value)
        return 0

    def pop_reasoning_metadata(self) -> dict[str, object]:
        """Return safe reasoning metadata without returning hidden reasoning text."""

        reasoning = self._last_reasoning
        self._last_reasoning = None
        metadata = {
            "present": self._last_reasoning_present or bool(reasoning),
            "characters": self._last_reasoning_characters or len(reasoning or ""),
        }
        self._last_reasoning_present = False
        self._last_reasoning_characters = 0
        return metadata

    @staticmethod
    def _stringify_raw_response(response: requests.Response) -> str:
        """Store safe provider metadata without serializing hidden reasoning."""

        try:
            payload = response.json()
            redacted_payload = OpenCodeGoAgent._redact_reasoning(payload)
            if isinstance(redacted_payload, dict):
                redacted_payload = dict(redacted_payload)
                redacted_payload["transport_http_status"] = getattr(
                    response, "status_code", None
                )
            return json.dumps(
                redacted_payload,
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
            if value.get("type") == "reasoning":
                return {"type": "reasoning", "content": "<redacted_reasoning>"}
            return {
                key: "<redacted_reasoning>"
                if key.lower()
                in {
                    "reasoning",
                    "reasoning_content",
                    "thinking",
                    "encrypted_content",
                }
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
    "DEFAULT_PROTOCOL",
    "OpenCodeGoAgent",
    "OpenCodeGoConfig",
    "OUTPUT_FORMAT",
    "PROMPT_TEMPLATE",
]

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ProviderToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ProviderTurn:
    response_id: str | None = None
    tool_calls: list[ProviderToolCall] = field(default_factory=list)
    final_output: dict[str, Any] | None = None
    usage: dict[str, int] = field(default_factory=dict)


class ModelProvider(Protocol):
    def start(
        self,
        *,
        instructions: str,
        context: dict[str, Any],
        tool_names: list[str],
        model_name: str,
    ) -> ProviderTurn: ...

    def continue_with_tool_outputs(
        self,
        *,
        response_id: str | None,
        tool_outputs: list[dict[str, Any]],
        tool_names: list[str],
        model_name: str,
    ) -> ProviderTurn: ...


@dataclass
class ScriptedProviderTurn:
    tool_calls: list[ProviderToolCall] = field(default_factory=list)
    final_output: dict[str, Any] | None = None


class ScriptedProvider:
    def __init__(self, turns: list[ScriptedProviderTurn]) -> None:
        self._turns = turns
        self._index = 0

    def start(
        self,
        *,
        instructions: str,
        context: dict[str, Any],
        tool_names: list[str],
        model_name: str,
    ) -> ProviderTurn:
        del instructions, context, tool_names, model_name
        return self._next_turn()

    def continue_with_tool_outputs(
        self,
        *,
        response_id: str | None,
        tool_outputs: list[dict[str, Any]],
        tool_names: list[str],
        model_name: str,
    ) -> ProviderTurn:
        del response_id, tool_outputs, tool_names, model_name
        return self._next_turn()

    def _next_turn(self) -> ProviderTurn:
        if self._index >= len(self._turns):
            raise RuntimeError("scripted provider exhausted")
        turn = self._turns[self._index]
        self._index += 1
        return ProviderTurn(
            response_id=f"scripted_{self._index}",
            tool_calls=turn.tool_calls,
            final_output=turn.final_output,
        )


class OpenAIResponsesProvider:
    def __init__(self, client=None) -> None:
        self._client = client

    def _client_or_default(self):
        if self._client is not None:
            return self._client
        from openai import OpenAI

        self._client = OpenAI()
        return self._client

    def start(
        self,
        *,
        instructions: str,
        context: dict[str, Any],
        tool_names: list[str],
        model_name: str,
    ) -> ProviderTurn:
        client = self._client_or_default()
        response = client.responses.create(
            model=model_name,
            instructions=instructions,
            input=json.dumps(context),
            tools=[self._tool_schema(name) for name in tool_names],
        )
        return self._parse_response(response)

    def continue_with_tool_outputs(
        self,
        *,
        response_id: str | None,
        tool_outputs: list[dict[str, Any]],
        tool_names: list[str],
        model_name: str,
    ) -> ProviderTurn:
        client = self._client_or_default()
        response = client.responses.create(
            model=model_name,
            previous_response_id=response_id,
            tools=[self._tool_schema(name) for name in tool_names],
            input=tool_outputs,
        )
        return self._parse_response(response)

    def _tool_schema(self, name: str) -> dict[str, Any]:
        return {
            "type": "function",
            "name": name,
            "description": f"HypoForge tool: {name}",
            "parameters": {
                "type": "object",
                "additionalProperties": True,
            },
        }

    def _parse_response(self, response) -> ProviderTurn:
        tool_calls: list[ProviderToolCall] = []
        output = getattr(response, "output", []) or []
        for item in output:
            if getattr(item, "type", None) == "function_call":
                arguments = getattr(item, "arguments", "{}")
                tool_calls.append(
                    ProviderToolCall(
                        call_id=getattr(item, "call_id"),
                        name=getattr(item, "name"),
                        arguments=json.loads(arguments),
                    )
                )
        if tool_calls:
            return ProviderTurn(response_id=getattr(response, "id", None), tool_calls=tool_calls)

        final_output = None
        parsed = getattr(response, "output_parsed", None)
        if parsed is not None:
            final_output = parsed if isinstance(parsed, dict) else json.loads(json.dumps(parsed))
        elif getattr(response, "output_text", None):
            final_output = json.loads(response.output_text)
        return ProviderTurn(
            response_id=getattr(response, "id", None),
            final_output=final_output,
            usage={
                "input_tokens": getattr(getattr(response, "usage", None), "input_tokens", 0),
                "output_tokens": getattr(getattr(response, "usage", None), "output_tokens", 0),
            },
        )


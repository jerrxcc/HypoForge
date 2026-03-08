from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from hypoforge.tools.schemas import TOOL_ARG_MODELS

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
        output_schema: dict[str, Any] | None = None,
    ) -> ProviderTurn: ...

    def continue_with_tool_outputs(
        self,
        *,
        response_id: str | None,
        tool_outputs: list[dict[str, Any]],
        tool_names: list[str],
        model_name: str,
        output_schema: dict[str, Any] | None = None,
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
        output_schema: dict[str, Any] | None = None,
    ) -> ProviderTurn:
        del instructions, context, tool_names, model_name, output_schema
        return self._next_turn()

    def continue_with_tool_outputs(
        self,
        *,
        response_id: str | None,
        tool_outputs: list[dict[str, Any]],
        tool_names: list[str],
        model_name: str,
        output_schema: dict[str, Any] | None = None,
    ) -> ProviderTurn:
        del response_id, tool_outputs, tool_names, model_name, output_schema
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
    def __init__(self, client=None, api_key: str | None = None, base_url: str | None = None) -> None:
        self._client = client
        self._api_key = api_key
        self._base_url = base_url

    def _client_or_default(self):
        if self._client is not None:
            return self._client
        from openai import OpenAI

        kwargs: dict[str, Any] = {}
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if self._base_url:
            kwargs["base_url"] = self._base_url
        self._client = OpenAI(**kwargs)
        return self._client

    def start(
        self,
        *,
        instructions: str,
        context: dict[str, Any],
        tool_names: list[str],
        model_name: str,
        output_schema: dict[str, Any] | None = None,
    ) -> ProviderTurn:
        client = self._client_or_default()
        request: dict[str, Any] = {
            "model": model_name,
            "instructions": instructions,
            "input": json.dumps(context),
            "tools": [self._tool_schema(name) for name in tool_names],
        }
        if output_schema is not None:
            request["text"] = self._response_format(f"{model_name}_output", output_schema)
        response = client.responses.create(**request)
        return self._parse_response(response)

    def continue_with_tool_outputs(
        self,
        *,
        response_id: str | None,
        tool_outputs: list[dict[str, Any]],
        tool_names: list[str],
        model_name: str,
        output_schema: dict[str, Any] | None = None,
    ) -> ProviderTurn:
        client = self._client_or_default()
        request: dict[str, Any] = {
            "model": model_name,
            "previous_response_id": response_id,
            "tools": [self._tool_schema(name) for name in tool_names],
            "input": tool_outputs,
        }
        if output_schema is not None:
            request["text"] = self._response_format(f"{model_name}_output", output_schema)
        response = client.responses.create(**request)
        return self._parse_response(response)

    def _tool_schema(self, name: str) -> dict[str, Any]:
        args_model = TOOL_ARG_MODELS[name]
        parameters = args_model.model_json_schema()
        if "title" in parameters:
            parameters.pop("title")
        return {
            "type": "function",
            "name": name,
            "description": f"HypoForge tool: {name}",
            "parameters": parameters,
        }

    def _response_format(self, name: str, output_schema: dict[str, Any]) -> dict[str, Any]:
        schema = self._normalize_response_schema(dict(output_schema))
        schema.pop("title", None)
        normalized_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:64]
        return {
            "format": {
                "type": "json_schema",
                "name": normalized_name,
                "schema": schema,
                "strict": True,
            }
        }

    def _normalize_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        schema_type = schema.get("type")
        if schema_type == "object":
            schema.setdefault("additionalProperties", False)
            properties = schema.get("properties") or {}
            schema["required"] = list(properties.keys())
            for prop_schema in properties.values():
                if isinstance(prop_schema, dict):
                    self._normalize_response_schema(prop_schema)
        if schema_type == "array":
            items = schema.get("items")
            if isinstance(items, dict):
                self._normalize_response_schema(items)
        for def_schema in (schema.get("$defs") or {}).values():
            if isinstance(def_schema, dict):
                self._normalize_response_schema(def_schema)
        any_of = schema.get("anyOf") or []
        for item in any_of:
            if isinstance(item, dict):
                self._normalize_response_schema(item)
        return schema

    def _parse_response(self, response) -> ProviderTurn:
        tool_calls: list[ProviderToolCall] = []
        usage = {
            "input_tokens": getattr(getattr(response, "usage", None), "input_tokens", 0),
            "output_tokens": getattr(getattr(response, "usage", None), "output_tokens", 0),
        }
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
            return ProviderTurn(
                response_id=getattr(response, "id", None),
                tool_calls=tool_calls,
                usage=usage,
            )

        final_output = None
        parsed = getattr(response, "output_parsed", None)
        if parsed is not None:
            final_output = parsed if isinstance(parsed, dict) else json.loads(json.dumps(parsed))
        elif getattr(response, "output_text", None):
            final_output = json.loads(response.output_text)
        return ProviderTurn(
            response_id=getattr(response, "id", None),
            final_output=final_output,
            usage=usage,
        )

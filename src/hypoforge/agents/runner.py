from __future__ import annotations

import json
from typing import Any
from pydantic import ValidationError


class AgentRunner:
    def __init__(
        self,
        *,
        provider,
        tool_invoker,
        output_model,
        agent_name: str,
        model_name: str,
        max_tool_steps: int,
        repair_output=None,
    ) -> None:
        self._provider = provider
        self._tool_invoker = tool_invoker
        self._output_model = output_model
        self._agent_name = agent_name
        self._model_name = model_name
        self._max_tool_steps = max_tool_steps
        self._repair_output = repair_output

    def execute(
        self,
        *,
        instructions: str,
        context: dict[str, Any],
        tool_names: list[str],
    ):
        turn = self._provider.start(
            instructions=instructions,
            context=context,
            tool_names=tool_names,
            model_name=self._model_name,
            output_schema=self._output_model.model_json_schema(),
        )
        turn, _step_count = self._consume_turns(turn, tool_names)
        return self._validate_final_output(turn, context, tool_names)

    def _consume_turns(self, turn, tool_names: list[str], step_count: int = 0):
        while turn.final_output is None:
            if step_count >= self._max_tool_steps:
                raise RuntimeError(f"{self._agent_name} exceeded tool step budget")
            tool_outputs = []
            for call in turn.tool_calls:
                if call.name not in tool_names:
                    raise ValueError(f"tool not allowed for {self._agent_name}: {call.name}")
                trace_context = {
                    "request_id": turn.response_id,
                    "input_tokens": turn.usage.get("input_tokens", 0),
                    "output_tokens": turn.usage.get("output_tokens", 0),
                }
                result = self._tool_invoker(call.name, call.arguments, trace_context)
                output = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": output,
                    }
                )
            turn = self._provider.continue_with_tool_outputs(
                response_id=turn.response_id,
                tool_outputs=tool_outputs,
                tool_names=tool_names,
                model_name=self._model_name,
                output_schema=self._output_model.model_json_schema(),
            )
            step_count += 1
        return turn, step_count

    def _validate_final_output(self, turn, context: dict[str, Any], tool_names: list[str]):
        try:
            return self._output_model.model_validate(turn.final_output)
        except ValidationError as initial_error:
            retry_prompt = self._schema_retry_prompt(initial_error)
            retry_turn = self._provider.continue_with_tool_outputs(
                response_id=turn.response_id,
                tool_outputs=[retry_prompt],
                tool_names=tool_names,
                model_name=self._model_name,
                output_schema=self._output_model.model_json_schema(),
            )
            retry_turn, _ = self._consume_turns(retry_turn, tool_names)
            try:
                return self._output_model.model_validate(retry_turn.final_output)
            except ValidationError:
                if self._repair_output is None:
                    raise
                repaired = self._repair_output(retry_turn.final_output or {}, context)
                return self._output_model.model_validate(repaired)

    def _schema_retry_prompt(self, error: ValidationError) -> dict[str, Any]:
        return {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        f"Your previous structured output for {self._agent_name} failed schema validation. "
                        f"Return corrected JSON only. Validation errors: {error}"
                    ),
                }
            ],
        }

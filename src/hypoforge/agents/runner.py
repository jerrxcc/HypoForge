from __future__ import annotations

import json
from typing import Any


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
    ) -> None:
        self._provider = provider
        self._tool_invoker = tool_invoker
        self._output_model = output_model
        self._agent_name = agent_name
        self._model_name = model_name
        self._max_tool_steps = max_tool_steps

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
        step_count = 0
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
        return self._output_model.model_validate(turn.final_output)

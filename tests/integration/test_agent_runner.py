from hypoforge.agents.providers import ProviderToolCall, ScriptedProvider, ScriptedProviderTurn
from hypoforge.agents.runner import AgentRunner
from hypoforge.domain.schemas import RetrievalSummary
import json


def test_agent_runner_executes_allowed_tool_calls() -> None:
    provider = ScriptedProvider(
        [
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_1",
                        name="search_openalex_works",
                        arguments={
                            "query": "protein binder design",
                            "year_from": 2018,
                            "year_to": 2026,
                            "limit": 5,
                        },
                    )
                ]
            ),
            ScriptedProviderTurn(
                final_output={
                    "canonical_topic": "protein binder design",
                    "query_variants_used": ["protein binder design"],
                    "search_notes": ["used OpenAlex"],
                    "selected_paper_ids": ["p1", "p2"],
                    "excluded_paper_ids": [],
                    "coverage_assessment": "good",
                    "needs_broader_search": False,
                }
            ),
        ]
    )

    calls = []

    def invoke(tool_name: str, payload: dict, trace_context: dict) -> dict:
        calls.append((tool_name, payload))
        assert trace_context["request_id"] == "scripted_1"
        return {"papers": [{"paper_id": "p1"}, {"paper_id": "p2"}]}

    runner = AgentRunner(
        provider=provider,
        tool_invoker=invoke,
        output_model=RetrievalSummary,
        agent_name="retrieval",
        model_name="gpt-5.4",
        max_tool_steps=2,
    )

    summary = runner.execute(
        instructions="Retrieve papers",
        context={"topic": "protein binder design"},
        tool_names=["search_openalex_works"],
    )

    assert summary.selected_paper_ids == ["p1", "p2"]
    assert calls[0][0] == "search_openalex_works"


def test_agent_runner_stringifies_tool_outputs_for_provider() -> None:
    captured_tool_outputs = []

    class CapturingProvider(ScriptedProvider):
        def continue_with_tool_outputs(
            self,
            *,
            response_id,
            tool_outputs,
            tool_names,
            model_name,
            output_schema=None,
        ):
            del response_id, tool_names, model_name, output_schema
            captured_tool_outputs.extend(tool_outputs)
            return super().continue_with_tool_outputs(
                response_id="scripted_1",
                tool_outputs=tool_outputs,
                tool_names=[],
                model_name="gpt-5.4",
                output_schema=None,
            )

    provider = CapturingProvider(
        [
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_1",
                        name="search_openalex_works",
                        arguments={"query": "x", "year_from": 2018, "year_to": 2026, "limit": 5},
                    )
                ]
            ),
            ScriptedProviderTurn(
                final_output={
                    "canonical_topic": "x",
                    "query_variants_used": ["x"],
                    "search_notes": [],
                    "selected_paper_ids": ["p1"],
                    "excluded_paper_ids": [],
                    "coverage_assessment": "good",
                    "needs_broader_search": False,
                }
            ),
        ]
    )

    runner = AgentRunner(
        provider=provider,
        tool_invoker=lambda tool_name, payload, trace_context: {"papers": [{"paper_id": "p1"}]},
        output_model=RetrievalSummary,
        agent_name="retrieval",
        model_name="gpt-5.4",
        max_tool_steps=2,
    )

    runner.execute(
        instructions="Retrieve papers",
        context={"topic": "x"},
        tool_names=["search_openalex_works"],
    )

    assert isinstance(captured_tool_outputs[0]["output"], str)
    assert json.loads(captured_tool_outputs[0]["output"]) == {"papers": [{"paper_id": "p1"}]}


def test_agent_runner_retries_once_after_output_validation_failure() -> None:
    continue_inputs = []

    class CapturingProvider(ScriptedProvider):
        def continue_with_tool_outputs(
            self,
            *,
            response_id,
            tool_outputs,
            tool_names,
            model_name,
            output_schema=None,
        ):
            del response_id, tool_names, model_name, output_schema
            continue_inputs.append(tool_outputs)
            return super().continue_with_tool_outputs(
                response_id="scripted_1",
                tool_outputs=tool_outputs,
                tool_names=[],
                model_name="gpt-5.4",
                output_schema=None,
            )

    provider = CapturingProvider(
        [
            ScriptedProviderTurn(
                final_output={
                    "canonical_topic": "x",
                    "query_variants_used": ["x"],
                    "search_notes": [],
                    "selected_paper_ids": ["p1"],
                    "excluded_paper_ids": [],
                    "needs_broader_search": False,
                }
            ),
            ScriptedProviderTurn(
                final_output={
                    "canonical_topic": "x",
                    "query_variants_used": ["x"],
                    "search_notes": ["retry fixed schema"],
                    "selected_paper_ids": ["p1"],
                    "excluded_paper_ids": [],
                    "coverage_assessment": "good",
                    "needs_broader_search": False,
                }
            ),
        ]
    )

    runner = AgentRunner(
        provider=provider,
        tool_invoker=lambda tool_name, payload, trace_context: {},
        output_model=RetrievalSummary,
        agent_name="retrieval",
        model_name="gpt-5.4",
        max_tool_steps=2,
    )

    summary = runner.execute(
        instructions="Retrieve papers",
        context={"topic": "x"},
        tool_names=["search_openalex_works"],
    )

    assert summary.coverage_assessment == "good"
    assert "failed schema validation" in json.dumps(continue_inputs[0])


def test_agent_runner_uses_repair_output_after_retry_still_invalid() -> None:
    provider = ScriptedProvider(
        [
            ScriptedProviderTurn(
                final_output={
                    "canonical_topic": "x",
                    "query_variants_used": ["x"],
                    "search_notes": [],
                    "selected_paper_ids": ["p1"],
                    "excluded_paper_ids": [],
                    "needs_broader_search": False,
                }
            ),
            ScriptedProviderTurn(
                final_output={
                    "canonical_topic": "x",
                    "query_variants_used": ["x"],
                    "search_notes": ["still incomplete"],
                    "selected_paper_ids": ["p1"],
                    "excluded_paper_ids": [],
                    "needs_broader_search": False,
                }
            ),
        ]
    )

    runner = AgentRunner(
        provider=provider,
        tool_invoker=lambda tool_name, payload, trace_context: {},
        output_model=RetrievalSummary,
        agent_name="retrieval",
        model_name="gpt-5.4",
        max_tool_steps=2,
        repair_output=lambda output, context: {
            **output,
            "canonical_topic": output.get("canonical_topic") or context["topic"],
            "coverage_assessment": "medium",
        },
    )

    summary = runner.execute(
        instructions="Retrieve papers",
        context={"topic": "x"},
        tool_names=["search_openalex_works"],
    )

    assert summary.coverage_assessment == "medium"

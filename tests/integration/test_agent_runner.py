import pytest

from hypoforge.agents.providers import (
    ProviderToolCall,
    ScriptedProvider,
    ScriptedProviderTurn,
)
from hypoforge.agents.runner import AgentRunner
from hypoforge.application.budget import ToolStepBudgetExceededError
from pydantic import ValidationError

from hypoforge.domain.schemas import CriticSummary, EvidenceCard, RetrievalSummary, RunRequest
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.errors import RecoverableToolInputError
from hypoforge.tools.workspace_tools import WorkspaceTools
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
        model_name="gpt-5.4-mini",
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
                model_name="gpt-5.4-mini",
                output_schema=None,
            )

    provider = CapturingProvider(
        [
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_1",
                        name="search_openalex_works",
                        arguments={
                            "query": "x",
                            "year_from": 2018,
                            "year_to": 2026,
                            "limit": 5,
                        },
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
        tool_invoker=lambda tool_name, payload, trace_context: {
            "papers": [{"paper_id": "p1"}]
        },
        output_model=RetrievalSummary,
        agent_name="retrieval",
        model_name="gpt-5.4-mini",
        max_tool_steps=2,
    )

    runner.execute(
        instructions="Retrieve papers",
        context={"topic": "x"},
        tool_names=["search_openalex_works"],
    )

    assert isinstance(captured_tool_outputs[0]["output"], str)
    assert json.loads(captured_tool_outputs[0]["output"]) == {
        "papers": [{"paper_id": "p1"}]
    }


def test_agent_runner_returns_recoverable_tool_input_errors_to_provider() -> None:
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
                model_name="gpt-5.4-mini",
                output_schema=None,
            )

    provider = CapturingProvider(
        [
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_bad",
                        name="search_openalex_works",
                        arguments={
                            "query": "bad id",
                            "year_from": 2018,
                            "year_to": 2026,
                            "limit": 5,
                        },
                    )
                ]
            ),
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_fixed",
                        name="search_openalex_works",
                        arguments={
                            "query": "fixed id",
                            "year_from": 2018,
                            "year_to": 2026,
                            "limit": 5,
                        },
                    )
                ]
            ),
            ScriptedProviderTurn(
                final_output={
                    "canonical_topic": "x",
                    "query_variants_used": ["x"],
                    "search_notes": ["corrected tool input"],
                    "selected_paper_ids": ["p1"],
                    "excluded_paper_ids": [],
                    "coverage_assessment": "good",
                    "needs_broader_search": False,
                }
            ),
        ]
    )
    call_count = 0

    def invoke(tool_name: str, payload: dict, trace_context: dict) -> dict:
        nonlocal call_count
        del tool_name, trace_context
        call_count += 1
        if payload["query"] == "bad id":
            raise RecoverableToolInputError(
                "invalid evidence id",
                instruction="Use exact EvidenceCard.evidence_id values.",
            )
        return {"papers": [{"paper_id": "p1"}]}

    runner = AgentRunner(
        provider=provider,
        tool_invoker=invoke,
        output_model=RetrievalSummary,
        agent_name="retrieval",
        model_name="gpt-5.4-mini",
        max_tool_steps=3,
    )

    summary = runner.execute(
        instructions="Retrieve papers",
        context={"topic": "x"},
        tool_names=["search_openalex_works"],
    )

    first_output = json.loads(captured_tool_outputs[0]["output"])
    assert first_output["error"]["type"] == "tool_input_validation_error"
    assert first_output["error"]["retryable"] is True
    assert first_output["error"]["instruction"] == "Use exact EvidenceCard.evidence_id values."
    assert json.loads(captured_tool_outputs[1]["output"]) == {
        "papers": [{"paper_id": "p1"}]
    }
    assert call_count == 2
    assert summary.coverage_assessment == "good"


def test_agent_runner_recovers_invalid_conflict_evidence_ids(tmp_path) -> None:
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
                model_name="gpt-5.4-mini",
                output_schema=None,
            )

    invalid_cluster = {
        "cluster_id": "high_rate_stability_depends_on_architecture",
        "topic_axis": "high-rate stability depends on architecture",
        "supporting_evidence_ids": ["W4391361976_1"],
        "conflicting_evidence_ids": ["oa_W3107306211_1"],
        "conflict_type": "conditional_divergence",
        "critic_summary": "Architecture affects high-rate stability.",
        "confidence": 0.8,
    }
    valid_cluster = {
        **invalid_cluster,
        "supporting_evidence_ids": ["oa_W4391361976_1"],
    }
    provider = CapturingProvider(
        [
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_bad",
                        name="save_conflict_clusters",
                        arguments={"conflict_clusters": [invalid_cluster]},
                    )
                ]
            ),
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_fixed",
                        name="save_conflict_clusters",
                        arguments={"conflict_clusters": [valid_cluster]},
                    )
                ]
            ),
            ScriptedProviderTurn(
                final_output={
                    "clusters_created": 1,
                    "top_axes": ["high-rate stability"],
                    "critic_notes": ["corrected evidence id"],
                }
            ),
        ]
    )
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="solid-state battery electrolyte"))
    repo.save_evidence_cards(
        run.run_id,
        [
            _evidence_card("oa_W4391361976_1"),
            _evidence_card("oa_W3107306211_1"),
        ],
    )
    tools = WorkspaceTools(repository=repo)

    runner = AgentRunner(
        provider=provider,
        tool_invoker=lambda tool_name, payload, trace_context: tools.save_conflict_clusters(
            run.run_id, payload
        ),
        output_model=CriticSummary,
        agent_name="critic",
        model_name="gpt-5.4-mini",
        max_tool_steps=3,
    )

    summary = runner.execute(
        instructions="Save conflict clusters",
        context={"run_id": run.run_id},
        tool_names=["save_conflict_clusters"],
    )

    first_output = json.loads(captured_tool_outputs[0]["output"])
    assert first_output["error"]["type"] == "tool_input_validation_error"
    assert "W4391361976_1" in first_output["error"]["message"]
    assert json.loads(captured_tool_outputs[1]["output"]) == {
        "cluster_ids": ["high_rate_stability_depends_on_architecture"]
    }
    assert summary.clusters_created == 1
    clusters = repo.load_conflict_clusters(run.run_id)
    assert clusters[0].supporting_evidence_ids == ["oa_W4391361976_1"]


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
                model_name="gpt-5.4-mini",
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
        model_name="gpt-5.4-mini",
        max_tool_steps=2,
    )

    summary = runner.execute(
        instructions="Retrieve papers",
        context={"topic": "x"},
        tool_names=["search_openalex_works"],
    )

    assert summary.coverage_assessment == "good"
    assert "failed schema validation" in json.dumps(continue_inputs[0])


def test_agent_runner_raises_after_retry_still_invalid() -> None:
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
        model_name="gpt-5.4-mini",
        max_tool_steps=2,
    )

    with pytest.raises(ValidationError, match="coverage_assessment"):
        runner.execute(
            instructions="Retrieve papers",
            context={"topic": "x"},
            tool_names=["search_openalex_works"],
        )


def test_agent_runner_raises_tool_step_budget_when_provider_never_finishes() -> None:
    provider = ScriptedProvider(
        [
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_1",
                        name="search_openalex_works",
                        arguments={
                            "query": "x",
                            "year_from": 2018,
                            "year_to": 2026,
                            "limit": 5,
                        },
                    )
                ]
            ),
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_2",
                        name="search_openalex_works",
                        arguments={
                            "query": "x",
                            "year_from": 2018,
                            "year_to": 2026,
                            "limit": 5,
                        },
                    )
                ]
            ),
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_3",
                        name="search_openalex_works",
                        arguments={
                            "query": "x",
                            "year_from": 2018,
                            "year_to": 2026,
                            "limit": 5,
                        },
                    )
                ]
            ),
        ]
    )

    runner = AgentRunner(
        provider=provider,
        tool_invoker=lambda tool_name, payload, trace_context: {
            "papers": [{"paper_id": "p1"}]
        },
        output_model=RetrievalSummary,
        agent_name="retrieval",
        model_name="gpt-5.4-mini",
        max_tool_steps=2,
    )

    with pytest.raises(
        ToolStepBudgetExceededError, match="retrieval exceeded tool step budget"
    ):
        runner.execute(
            instructions="Retrieve papers",
            context={"topic": "x"},
            tool_names=["search_openalex_works"],
        )


def test_agent_runner_fails_fast_when_provider_turn_cannot_progress() -> None:
    class NoProgressProvider:
        def __init__(self) -> None:
            self.continue_calls = 0

        def start(
            self, *, instructions, context, tool_names, model_name, output_schema=None
        ):
            del instructions, context, tool_names, model_name, output_schema
            from hypoforge.agents.providers import ProviderTurn

            return ProviderTurn(response_id="stalled", tool_calls=[], final_output=None)

        def continue_with_tool_outputs(
            self,
            *,
            response_id,
            tool_outputs,
            tool_names,
            model_name,
            output_schema=None,
        ):
            del response_id, tool_outputs, tool_names, model_name, output_schema
            self.continue_calls += 1
            raise AssertionError(
                "provider should not be called again for a stalled turn"
            )

    provider = NoProgressProvider()
    runner = AgentRunner(
        provider=provider,
        tool_invoker=lambda tool_name, payload, trace_context: {},
        output_model=RetrievalSummary,
        agent_name="retrieval",
        model_name="gpt-5.4-mini",
        max_tool_steps=2,
    )

    with pytest.raises(
        RuntimeError, match="returned neither tool calls nor final output"
    ):
        runner.execute(
            instructions="Retrieve papers",
            context={"topic": "x"},
            tool_names=["search_openalex_works"],
        )

    assert provider.continue_calls == 0


def _evidence_card(evidence_id: str) -> EvidenceCard:
    return EvidenceCard(
        evidence_id=evidence_id,
        paper_id="p1",
        title="Paper",
        claim_text="Claim",
        system_or_material="System",
        intervention="Intervention",
        outcome="Outcome",
        direction="positive",
        confidence=0.8,
    )

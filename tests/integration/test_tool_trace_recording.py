from hypoforge.agents.providers import ProviderToolCall, ScriptedProvider, ScriptedProviderTurn
from hypoforge.agents.runner import AgentRunner
from hypoforge.domain.schemas import RetrievalSummary, RunRequest
from hypoforge.infrastructure.db.repository import RunRepository


def test_tool_trace_is_recorded_for_default_style_invoker(tmp_path) -> None:
    repo = RunRepository.from_sqlite_path(tmp_path / "app.db")
    run = repo.create_run(RunRequest(topic="protein binder design"))

    provider = ScriptedProvider(
        [
            ScriptedProviderTurn(
                tool_calls=[
                    ProviderToolCall(
                        call_id="call_1",
                        name="search_openalex_works",
                        arguments={"query": "protein binder design", "year_from": 2018, "year_to": 2026, "limit": 5},
                    )
                ]
            ),
            ScriptedProviderTurn(
                final_output={
                    "canonical_topic": "protein binder design",
                    "query_variants_used": ["protein binder design"],
                    "search_notes": [],
                    "selected_paper_ids": ["p1"],
                    "excluded_paper_ids": [],
                    "coverage_assessment": "good",
                    "needs_broader_search": False,
                }
            ),
        ]
    )

    def invoke(tool_name: str, payload: dict):
        repo.record_tool_trace(
            run_id=run.run_id,
            agent_name="retrieval",
            tool_name=tool_name,
            args=payload,
            result_summary={"count": 1},
            latency_ms=1,
            model_name="gpt-5.4",
            success=True,
        )
        return {"papers": [{"paper_id": "p1"}]}

    runner = AgentRunner(
        provider=provider,
        tool_invoker=invoke,
        output_model=RetrievalSummary,
        agent_name="retrieval",
        model_name="gpt-5.4",
        max_tool_steps=2,
    )

    runner.execute(
        instructions="Retrieve papers",
        context={"topic": "protein binder design"},
        tool_names=["search_openalex_works"],
    )

    traces = repo.list_tool_traces(run.run_id)
    assert len(traces) == 1
    assert traces[0]["tool_name"] == "search_openalex_works"

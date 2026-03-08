from hypoforge.agents.providers import ProviderToolCall, ScriptedProvider, ScriptedProviderTurn
from hypoforge.agents.runner import AgentRunner
from hypoforge.domain.schemas import RetrievalSummary


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

    def invoke(tool_name: str, payload: dict) -> dict:
        calls.append((tool_name, payload))
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

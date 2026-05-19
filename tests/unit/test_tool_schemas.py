from hypoforge.agents.providers import OpenAIResponsesProvider
from hypoforge.agents.prompts import prompt_for


def test_openai_provider_emits_function_schema_with_properties() -> None:
    provider = OpenAIResponsesProvider()

    schema = provider._tool_schema("search_openalex_works")

    assert schema["parameters"]["type"] == "object"
    assert "properties" in schema["parameters"]
    assert "query" in schema["parameters"]["properties"]


def test_openai_provider_emits_alpha_paper_content_schema_with_aliases() -> None:
    provider = OpenAIResponsesProvider()

    schema = provider._tool_schema("get_alphaxiv_paper_content")

    assert "url" in schema["parameters"]["properties"]
    assert "fullText" in schema["parameters"]["properties"]


def test_conflict_cluster_schema_requires_exact_loaded_evidence_ids() -> None:
    provider = OpenAIResponsesProvider()

    schema = provider._tool_schema("save_conflict_clusters")
    cluster_schema = schema["parameters"]["$defs"]["ConflictCluster"]

    for field_name in ("supporting_evidence_ids", "conflicting_evidence_ids"):
        description = cluster_schema["properties"][field_name]["description"]
        assert "Exact EvidenceCard.evidence_id values" in description
        assert "do not use paper_id" in description


def test_critic_prompt_requires_exact_loaded_evidence_ids() -> None:
    prompt = prompt_for("critic")

    assert "load_evidence_cards" in prompt
    assert "Use only exact evidence_id values" in prompt
    assert "Do not derive evidence IDs from paper_id" in prompt

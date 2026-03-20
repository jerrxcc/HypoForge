from hypoforge.agents.providers import OpenAIResponsesProvider


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

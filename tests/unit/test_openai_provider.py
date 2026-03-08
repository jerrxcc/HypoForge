from unittest.mock import patch

from hypoforge.agents.providers import OpenAIResponsesProvider


def test_openai_provider_passes_api_key_and_base_url() -> None:
    with patch("openai.OpenAI") as client_cls:
        provider = OpenAIResponsesProvider(api_key="test-key", base_url="https://example.com/v1")

        provider._client_or_default()

    client_cls.assert_called_once_with(api_key="test-key", base_url="https://example.com/v1")


def test_openai_provider_builds_json_schema_response_format() -> None:
    from hypoforge.domain.schemas import RetrievalSummary

    provider = OpenAIResponsesProvider()

    response_format = provider._response_format("retrieval_summary", RetrievalSummary.model_json_schema())

    assert response_format["format"]["type"] == "json_schema"
    assert response_format["format"]["name"] == "retrieval_summary"
    assert response_format["format"]["strict"] is True
    assert response_format["format"]["schema"]["additionalProperties"] is False
    assert set(response_format["format"]["schema"]["required"]) == set(
        response_format["format"]["schema"]["properties"].keys()
    )


def test_openai_provider_sanitizes_response_format_name() -> None:
    provider = OpenAIResponsesProvider()

    response_format = provider._response_format("gpt-5.4_output", {"type": "object", "properties": {"x": {"type": "string"}}})

    assert response_format["format"]["name"] == "gpt-5_4_output"


def test_openai_provider_keeps_usage_on_tool_call_turns() -> None:
    class Usage:
        input_tokens = 61
        output_tokens = 431

    class FunctionCall:
        type = "function_call"
        call_id = "call_1"
        name = "search_openalex_works"
        arguments = '{"query":"battery"}'

    class Response:
        id = "resp_123"
        output = [FunctionCall()]
        usage = Usage()

    provider = OpenAIResponsesProvider()

    turn = provider._parse_response(Response())

    assert turn.response_id == "resp_123"
    assert turn.tool_calls[0].name == "search_openalex_works"
    assert turn.usage == {"input_tokens": 61, "output_tokens": 431}

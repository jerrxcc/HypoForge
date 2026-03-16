from hypoforge.application import services
from hypoforge.config import Settings


def test_build_default_services_passes_openalex_api_key_to_connector(tmp_path, monkeypatch) -> None:
    seen: dict[str, str | None] = {"api_key": None}

    class FakeOpenAlexConnector:
        def __init__(self, client=None, api_key: str | None = None) -> None:
            del client
            seen["api_key"] = api_key

    monkeypatch.setattr(services, "OpenAlexConnector", FakeOpenAlexConnector)

    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'app.db'}",
        openalex_api_key="openalex-secret",
    )

    services.build_default_services(settings)

    assert seen["api_key"] == "openalex-secret"


def test_build_default_services_passes_semantic_scholar_api_key_to_connector(
    tmp_path,
    monkeypatch,
) -> None:
    seen: dict[str, str | None] = {"api_key": None}

    class FakeSemanticScholarConnector:
        def __init__(self, client=None, api_key: str | None = None) -> None:
            del client
            seen["api_key"] = api_key

    monkeypatch.setattr(services, "SemanticScholarConnector", FakeSemanticScholarConnector)

    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'app.db'}",
        semantic_scholar_api_key="semantic-scholar-secret",
    )

    services.build_default_services(settings)

    assert seen["api_key"] == "semantic-scholar-secret"


def test_build_default_services_passes_request_timeout_to_provider(tmp_path, monkeypatch) -> None:
    seen: dict[str, object | None] = {"timeout_seconds": None}

    class FakeProvider:
        def __init__(self, client=None, api_key=None, base_url=None, timeout_seconds=None) -> None:
            del client, api_key, base_url
            seen["timeout_seconds"] = timeout_seconds

    monkeypatch.setattr(services, "OpenAIResponsesProvider", FakeProvider)

    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'app.db'}",
        request_timeout_seconds=45,
    )

    services.build_default_services(settings)

    assert seen["timeout_seconds"] == 45

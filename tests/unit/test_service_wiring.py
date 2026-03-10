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

from hypoforge.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_env == "dev"
    assert settings.max_selected_papers == 36
    assert settings.max_tool_steps_retrieval == 12


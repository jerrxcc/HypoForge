from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model_retrieval: str = "gpt-5.4"
    openai_model_review: str = "gpt-5-mini"
    openai_model_critic: str = "gpt-5.4"
    openai_model_planner: str = "gpt-5.4"

    openalex_api_key: str = ""
    semantic_scholar_api_key: str = ""
    database_url: str = "sqlite:///./hypoforge.db"
    raw_response_cache_ttl_seconds: int = 604800
    normalized_paper_cache_ttl_seconds: int = 2592000
    evidence_cache_ttl_seconds: int = 2592000

    max_selected_papers: int = 36
    max_tool_steps_retrieval: int = 12
    max_tool_steps_review: int = 6
    max_tool_steps_critic: int = 4
    max_tool_steps_planner: int = 4
    max_openalex_calls_per_run: int = 20
    max_s2_calls_per_run: int = 20
    request_timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

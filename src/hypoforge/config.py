from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReflectionSettings(BaseSettings):
    """Configuration for the reflection-correction loop system."""

    max_stage_iterations: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum iterations per stage before giving up",
    )
    max_cross_stage_iterations: int = Field(
        default=2,
        ge=1,
        le=3,
        description="Maximum cross-stage backtracking iterations",
    )
    retrieval_quality_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for retrieval stage",
    )
    review_quality_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for review stage",
    )
    critic_quality_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for critic stage",
    )
    planner_quality_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for planner stage",
    )
    enable_multi_perspective: bool = Field(
        default=True,
        description="Enable multi-perspective critique mode",
    )
    critic_perspectives: list[str] = Field(
        default=["methodological", "statistical", "domain"],
        description="List of critique perspectives to use",
    )
    enable_reflection: bool = Field(
        default=True,
        description="Globally enable/disable the reflection system",
    )

    model_config = SettingsConfigDict(
        env_prefix="REFLECTION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ValidationSettings(BaseSettings):
    """Configuration for the validation agents system."""

    enable_validation_agents: bool = Field(
        default=True,
        description="Globally enable/disable validation agents",
    )
    max_backtrack_per_stage: int = Field(
        default=2,
        ge=1,
        le=4,
        description="Maximum backtracks allowed per stage",
    )
    max_total_backtrack: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum total backtracks allowed per run",
    )
    backtrack_depth: int = Field(
        default=2,
        ge=1,
        le=3,
        description="Maximum stages to backtrack",
    )

    # Thresholds for validation decisions
    min_valid_evidence: int = Field(
        default=10,
        ge=3,
        le=20,
        description="Minimum valid evidence cards required",
    )
    min_conflict_coverage: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum conflict coverage ratio",
    )
    min_quality_score: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for hypotheses",
    )

    # Evidence validation thresholds
    evidence_completeness_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum evidence completeness score",
    )
    evidence_accuracy_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum evidence accuracy score",
    )
    evidence_relevance_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum evidence relevance score",
    )

    # Conflict detection thresholds
    conflict_intensity_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum conflict intensity for reporting",
    )
    max_homogeneity_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Maximum allowed evidence homogeneity",
    )

    # Quality assessment thresholds
    novelty_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for novelty dimension",
    )
    feasibility_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for feasibility dimension",
    )
    evidence_support_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for evidence support dimension",
    )
    conflict_utilization_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Weight for conflict utilization dimension",
    )

    # Model configuration for validators
    model_evidence_validator: str = Field(
        default="gpt-5-mini",
        description="Model for evidence validation",
    )
    model_conflict_detector: str = Field(
        default="gpt-5.4",
        description="Model for conflict detection",
    )
    model_quality_assessor: str = Field(
        default="gpt-5.4",
        description="Model for quality assessment",
    )
    model_feedback_synthesizer: str = Field(
        default="gpt-5-mini",
        description="Model for feedback synthesis",
    )

    model_config = SettingsConfigDict(
        env_prefix="VALIDATION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    frontend_allowed_origins: list[str] = ["http://127.0.0.1:3000"]

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
    review_batch_size: int = 6
    max_tool_steps_retrieval: int = 12
    max_tool_steps_review: int = 6
    max_tool_steps_critic: int = 4
    max_tool_steps_planner: int = 4
    max_openalex_calls_per_run: int = 20
    max_s2_calls_per_run: int = 20
    request_timeout_seconds: int = 30

    reflection_settings: ReflectionSettings = Field(
        default_factory=ReflectionSettings,
        description="Reflection-correction loop configuration",
    )

    validation_settings: ValidationSettings = Field(
        default_factory=ValidationSettings,
        description="Validation agents configuration",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import logging
from math import ceil
from time import perf_counter
from typing import Callable

from hypoforge.agents.prompts import prompt_for
from hypoforge.agents.reflection import ReflectionAgent
from hypoforge.agents.providers import OpenAIResponsesProvider
from hypoforge.agents.runner import AgentRunner
from hypoforge.agents.validation_base import ValidationAgentRegistry
from hypoforge.application.budget import RunBudgetTracker
from hypoforge.application.coordinator import RunCoordinator
from hypoforge.application.evidence_cache import (
    load_cached_evidence_cards_for_papers,
    save_evidence_cards_to_cache,
)
from hypoforge.application.repair import (
    repair_retrieval_output,
    repair_review_output,
    repair_critic_output,
    repair_planner_output,
)
from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.application.stage_graph import StageNavigator
from hypoforge.config import ReflectionSettings, Settings, ValidationSettings
from hypoforge.domain.schemas import (
    CriticSummary,
    PaperDetail,
    PlannerSummary,
    RetrievalSummary,
    ReviewSummary,
)
from hypoforge.infrastructure.connectors.alphaxiv import AlphaXivConnector
from hypoforge.infrastructure.connectors.openalex import OpenAlexConnector
from hypoforge.infrastructure.connectors.cached import (
    CachedAlphaXivConnector,
    CachedOpenAlexConnector,
    CachedSemanticScholarConnector,
)
from hypoforge.infrastructure.connectors.dedupe import merge_paper_details, paper_identity_key
from hypoforge.infrastructure.connectors.semantic_scholar import SemanticScholarConnector
from hypoforge.infrastructure.db.cache_repository import CacheRepository
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.render_tools import RenderTools
from hypoforge.tools.scholarly_tools import ScholarlyTools
from hypoforge.tools.workspace_tools import WorkspaceTools


@dataclass
class ServiceContainer:
    coordinator: RunCoordinator
    event_bus: object | None = None


_ALLOWED_EXECUTION_CONTEXT_KEYS = {
    "iteration_number",
    "is_retry",
    "previous_iteration_feedback",
    "accumulated_learnings",
    "validation_feedback",
}


def _merge_execution_context(
    base_context: dict[str, object],
    execution_context: dict[str, object] | None,
) -> dict[str, object]:
    if execution_context is None:
        return base_context

    unknown_keys = set(execution_context) - _ALLOWED_EXECUTION_CONTEXT_KEYS
    if unknown_keys:
        raise ValueError(
            f"unsupported execution context keys: {sorted(unknown_keys)}"
        )

    return {
        **base_context,
        **execution_context,
    }


def build_default_services(settings: Settings | None = None) -> ServiceContainer:
    """Build a fully-wired :class:`ServiceContainer` for production use.

    Initialises the repository, cache, OpenAI provider, all four agents,
    and the :class:`RunCoordinator` that orchestrates them.
    """
    settings = settings or Settings()
    repository = RunRepository.from_database_url(settings.database_url)
    cache_repository = CacheRepository(repository._session_factory)
    candidate_pools: dict[str, dict[str, PaperDetail]] = {}
    budget_trackers: dict[str, RunBudgetTracker] = {}
    provider = OpenAIResponsesProvider(
        api_key=settings.openai_api_key or None,
        base_url=settings.openai_base_url or None,
        timeout_seconds=settings.request_timeout_seconds,
        reasoning_effort=settings.openai_reasoning_effort or None,
    )
    renderer = ReportRenderer()
    logger = logging.getLogger(__name__)
    openalex_base = OpenAlexConnector(api_key=settings.openalex_api_key or None)
    semantic_scholar_base = SemanticScholarConnector(api_key=settings.semantic_scholar_api_key or None)
    alphaxiv_enabled = bool(settings.alphaxiv_access_token.strip())
    alphaxiv_base = (
        AlphaXivConnector(
            endpoint=settings.alphaxiv_mcp_endpoint,
            access_token=settings.alphaxiv_access_token or None,
        )
        if alphaxiv_enabled
        else None
    )
    review_prompt = prompt_for("review")
    review_prompt_version = sha256(review_prompt.encode("utf-8")).hexdigest()[:12]

    def make_tool_invoker(
        run_id: str,
        agent_name: str,
        model_name: str,
        *,
        stage_name: str = "unknown",
        selected_paper_ids: list[str] | None = None,
        append_evidence_cards: bool = False,
    ):
        candidate_pool = candidate_pools.setdefault(run_id, {})
        budget_tracker = budget_trackers.setdefault(
            run_id,
            RunBudgetTracker(
                max_openalex_calls=settings.max_openalex_calls_per_run,
                max_semantic_scholar_calls=settings.max_s2_calls_per_run,
                max_alphaxiv_calls=settings.max_alphaxiv_calls_per_run,
            ),
        )
        openalex = CachedOpenAlexConnector(
            openalex_base,
            cache_repository,
            ttl_seconds=settings.raw_response_cache_ttl_seconds,
            on_external_call=budget_tracker.register_openalex_call,
        )
        semantic_scholar = CachedSemanticScholarConnector(
            semantic_scholar_base,
            cache_repository,
            ttl_seconds=settings.raw_response_cache_ttl_seconds,
            normalized_ttl_seconds=settings.normalized_paper_cache_ttl_seconds,
            on_external_call=budget_tracker.register_semantic_scholar_call,
        )
        alphaxiv = (
            CachedAlphaXivConnector(
                alphaxiv_base,
                cache_repository,
                ttl_seconds=settings.raw_response_cache_ttl_seconds,
                on_external_call=budget_tracker.register_alphaxiv_call,
            )
            if alphaxiv_base is not None
            else None
        )

        def update_candidate_pool(result: dict) -> dict:
            for paper_payload in result.get("papers", []):
                paper = (
                    paper_payload
                    if isinstance(paper_payload, PaperDetail)
                    else PaperDetail.model_validate(paper_payload)
                )
                candidate_pool[paper.paper_id] = paper
            return result

        scholarly_tools = ScholarlyTools(
            openalex=openalex,
            semantic_scholar=semantic_scholar,
            alphaxiv=alphaxiv,
            repository=repository,
            paper_lookup=lambda paper_ids: _lookup_candidate_papers(candidate_pool, paper_ids),
        )
        workspace_tools = WorkspaceTools(
            repository=repository,
            selected_paper_ids=selected_paper_ids,
            append_evidence_cards=append_evidence_cards,
        )
        render_tools = RenderTools(repository=repository, renderer=renderer)
        registry = {
            "search_openalex_works": lambda payload: update_candidate_pool(scholarly_tools.search_openalex_works(payload)),
            "search_semantic_scholar_papers": lambda payload: update_candidate_pool(scholarly_tools.search_semantic_scholar_papers(payload)),
            "recommend_semantic_scholar_papers": lambda payload: update_candidate_pool(scholarly_tools.recommend_semantic_scholar_papers(payload)),
            "get_paper_details": lambda payload: update_candidate_pool(scholarly_tools.get_paper_details(payload)),
            "save_selected_papers": lambda payload: scholarly_tools.save_selected_papers(run_id, payload),
            "load_selected_papers": lambda payload: workspace_tools.load_selected_papers(run_id, payload),
            "save_evidence_cards": lambda payload: workspace_tools.save_evidence_cards(run_id, payload),
            "load_evidence_cards": lambda payload: workspace_tools.load_evidence_cards(run_id, payload),
            "save_conflict_clusters": lambda payload: workspace_tools.save_conflict_clusters(run_id, payload),
            "load_conflict_clusters": lambda payload: workspace_tools.load_conflict_clusters(run_id, payload),
            "save_hypotheses": lambda payload: workspace_tools.save_hypotheses(run_id, payload),
            "render_markdown_report": lambda payload: render_tools.render_markdown_report(run_id, payload),
        }
        if alphaxiv is not None:
            registry.update(
                {
                    "search_alphaxiv_embedding_similarity": lambda payload: update_candidate_pool(
                        scholarly_tools.search_alphaxiv_embedding_similarity(payload)
                    ),
                    "search_alphaxiv_full_text_papers": lambda payload: update_candidate_pool(
                        scholarly_tools.search_alphaxiv_full_text_papers(payload)
                    ),
                    "search_alphaxiv_agentic_paper_retrieval": lambda payload: update_candidate_pool(
                        scholarly_tools.search_alphaxiv_agentic_paper_retrieval(payload)
                    ),
                    "get_alphaxiv_paper_content": lambda payload: scholarly_tools.get_alphaxiv_paper_content(payload),
                    "answer_alphaxiv_pdf_queries": lambda payload: scholarly_tools.answer_alphaxiv_pdf_queries(payload),
                    "read_alphaxiv_github_repository": lambda payload: scholarly_tools.read_alphaxiv_github_repository(payload),
                }
            )

        def invoke(tool_name: str, payload: dict, trace_context: dict):
            attempt = 1
            if event_bus is not None:
                attempt = event_bus.get_attempt(run_id, stage_name)
                event_bus.publish(run_id, {
                    "type": "tool_start",
                    "stage_name": stage_name,
                    "attempt": attempt,
                    "agent_name": agent_name,
                    "tool_name": tool_name,
                })
            started_at = perf_counter()
            try:
                result = registry[tool_name](payload)
                summary = _summarize_tool_result(result)
                if trace_context.get("request_id"):
                    summary["request_id"] = trace_context["request_id"]
                latency_ms = max(1, int((perf_counter() - started_at) * 1000))

                def on_recorded(trace_dict: dict) -> None:
                    if event_bus is not None:
                        event_bus.publish(run_id, {
                            "type": "tool_complete",
                            "stage_name": stage_name,
                            "attempt": attempt,
                            "agent_name": agent_name,
                            "tool_name": tool_name,
                            "trace_id": trace_dict["id"],
                            "latency_ms": latency_ms,
                            "success": True,
                        })

                repository.record_tool_trace(
                    run_id=run_id,
                    agent_name=agent_name,
                    tool_name=tool_name,
                    stage_name=stage_name,
                    attempt=attempt,
                    args=payload,
                    result_summary=summary,
                    latency_ms=latency_ms,
                    model_name=model_name,
                    success=True,
                    input_tokens=trace_context.get("input_tokens"),
                    output_tokens=trace_context.get("output_tokens"),
                    on_recorded=on_recorded,
                )
                return result
            except Exception as exc:
                latency_ms = max(1, int((perf_counter() - started_at) * 1000))
                repository.record_tool_trace(
                    run_id=run_id,
                    agent_name=agent_name,
                    tool_name=tool_name,
                    stage_name=stage_name,
                    attempt=attempt,
                    args=payload,
                    result_summary={"error": type(exc).__name__},
                    latency_ms=latency_ms,
                    model_name=model_name,
                    success=False,
                    input_tokens=trace_context.get("input_tokens"),
                    output_tokens=trace_context.get("output_tokens"),
                    error_message=str(exc),
                )
                if event_bus is not None:
                    event_bus.publish(run_id, {
                        "type": "tool_complete",
                        "stage_name": stage_name,
                        "attempt": attempt,
                        "agent_name": agent_name,
                        "tool_name": tool_name,
                        "latency_ms": latency_ms,
                        "success": False,
                        "error": str(exc),
                    })
                raise

        return invoke

    def retrieval_agent(
        run_id: str,
        topic: str,
        constraints,
        *,
        execution_context: dict[str, object] | None = None,
    ) -> RetrievalSummary:
        runner = AgentRunner(
            provider=provider,
            tool_invoker=make_tool_invoker(run_id, "retrieval", settings.openai_model_retrieval, stage_name="retrieval"),
            output_model=RetrievalSummary,
            agent_name="retrieval",
            model_name=settings.openai_model_retrieval,
            max_tool_steps=settings.max_tool_steps_retrieval,
            repair_output=repair_retrieval_output,
        )
        retrieval_tool_names = [
            "search_openalex_works",
            "search_semantic_scholar_papers",
            "recommend_semantic_scholar_papers",
            "get_paper_details",
            "save_selected_papers",
        ]
        if alphaxiv_enabled:
            retrieval_tool_names.extend(
                [
                    "search_alphaxiv_embedding_similarity",
                    "search_alphaxiv_full_text_papers",
                    "search_alphaxiv_agentic_paper_retrieval",
                ]
            )
        return runner.execute(
            instructions=prompt_for("retrieval"),
            context=_merge_execution_context(
                {
                    "topic": topic,
                    "constraints": constraints.model_dump(),
                },
                execution_context,
            ),
            tool_names=retrieval_tool_names,
        )

    def review_agent(
        run_id: str,
        *,
        execution_context: dict[str, object] | None = None,
    ) -> ReviewSummary:
        selected_papers = repository.load_selected_papers(run_id)

        def review_batch(batch: list[PaperDetail]) -> ReviewSummary:
            cached_cards = load_cached_evidence_cards_for_papers(
                papers=batch,
                cache_repository=cache_repository,
                model_name=settings.openai_model_review,
                prompt_version=review_prompt_version,
            )
            if cached_cards is not None:
                repository.append_evidence_cards(run_id, cached_cards)
                repository.record_tool_trace(
                    run_id=run_id,
                    agent_name="review",
                    tool_name="evidence_extraction_cache_hit",
                    stage_name="review",
                    args={"run_id": run_id, "paper_ids": [paper.paper_id for paper in batch]},
                    result_summary={
                        "cache_hit": True,
                        "evidence_ids": [card.evidence_id for card in cached_cards[:5]],
                        "result_count": len(cached_cards),
                    },
                    latency_ms=1,
                    model_name=settings.openai_model_review,
                    success=True,
                )
                logger.info(
                    "review cache hit",
                    extra={"run_id": run_id, "cards": len(cached_cards), "paper_count": len(batch)},
                )
                return ReviewSummary(
                    papers_processed=len(batch),
                    evidence_cards_created=len(cached_cards),
                    coverage_summary="loaded from evidence cache",
                    dominant_axes=[],
                    low_confidence_paper_ids=[],
                )

            runner = AgentRunner(
                provider=provider,
                tool_invoker=make_tool_invoker(
                    run_id,
                    "review",
                    settings.openai_model_review,
                    stage_name="review",
                    selected_paper_ids=[paper.paper_id for paper in batch],
                    append_evidence_cards=True,
                ),
                output_model=ReviewSummary,
                agent_name="review",
                model_name=settings.openai_model_review,
                max_tool_steps=settings.max_tool_steps_review,
                repair_output=repair_review_output,
            )
            review_tool_names = ["load_selected_papers", "save_evidence_cards"]
            if alphaxiv_enabled:
                review_tool_names[1:1] = [
                    "get_alphaxiv_paper_content",
                    "answer_alphaxiv_pdf_queries",
                    "read_alphaxiv_github_repository",
                ]
            summary = runner.execute(
                instructions=review_prompt,
                context=_merge_execution_context(
                    {"run_id": run_id, "paper_ids": [paper.paper_id for paper in batch]},
                    execution_context,
                ),
                tool_names=review_tool_names,
            )
            save_evidence_cards_to_cache(
                run_id=run_id,
                papers=batch,
                repository=repository,
                cache_repository=cache_repository,
                model_name=settings.openai_model_review,
                prompt_version=review_prompt_version,
                ttl_seconds=settings.evidence_cache_ttl_seconds,
            )
            return summary

        return _review_papers_in_batches(
            selected_papers=selected_papers,
            batch_size=settings.review_batch_size,
            review_batch=review_batch,
        )

    def critic_agent(
        run_id: str,
        *,
        execution_context: dict[str, object] | None = None,
    ) -> CriticSummary:
        runner = AgentRunner(
            provider=provider,
            tool_invoker=make_tool_invoker(run_id, "critic", settings.openai_model_critic, stage_name="critic"),
            output_model=CriticSummary,
            agent_name="critic",
            model_name=settings.openai_model_critic,
            max_tool_steps=settings.max_tool_steps_critic,
            repair_output=repair_critic_output,
        )
        return runner.execute(
            instructions=prompt_for("critic"),
            context=_merge_execution_context({"run_id": run_id}, execution_context),
            tool_names=["load_evidence_cards", "save_conflict_clusters"],
        )

    def planner_agent(
        run_id: str,
        *,
        execution_context: dict[str, object] | None = None,
    ) -> PlannerSummary:
        runner = AgentRunner(
            provider=provider,
            tool_invoker=make_tool_invoker(run_id, "planner", settings.openai_model_planner, stage_name="planner"),
            output_model=PlannerSummary,
            agent_name="planner",
            model_name=settings.openai_model_planner,
            max_tool_steps=settings.max_tool_steps_planner,
            repair_output=repair_planner_output,
        )
        planner_tool_names = ["load_evidence_cards", "load_conflict_clusters", "save_hypotheses", "render_markdown_report"]
        if alphaxiv_enabled:
            planner_tool_names = [
                "load_selected_papers",
                "get_alphaxiv_paper_content",
                "answer_alphaxiv_pdf_queries",
                "read_alphaxiv_github_repository",
                *planner_tool_names,
            ]
        return runner.execute(
            instructions=prompt_for("planner"),
            context=_merge_execution_context({"run_id": run_id}, execution_context),
            tool_names=planner_tool_names,
        )

    # Create reflection agent if enabled
    reflection_agent: ReflectionAgent | None = None
    stage_navigator: StageNavigator | None = None
    if settings.reflection_settings.enable_reflection:
        retrieval_channels = [
            "openalex.search",
            "semantic_scholar.search",
            "semantic_scholar.recommend",
        ]
        if alphaxiv_enabled:
            retrieval_channels.extend(
                [
                    "alphaxiv.embedding_similarity_search",
                    "alphaxiv.full_text_papers_search",
                    "alphaxiv.agentic_paper_retrieval",
                ]
            )
        reflection_agent = ReflectionAgent(
            repository=repository,
            quality_thresholds={
                "retrieval": settings.reflection_settings.retrieval_quality_threshold,
                "review": settings.reflection_settings.review_quality_threshold,
                "critic": settings.reflection_settings.critic_quality_threshold,
                "planner": settings.reflection_settings.planner_quality_threshold,
            },
            enable_multi_perspective=settings.reflection_settings.enable_multi_perspective,
            perspectives=settings.reflection_settings.critic_perspectives,
            retrieval_channels=retrieval_channels,
        )
        stage_navigator = StageNavigator(repository=repository)
        logger.info(
            "Reflection system enabled",
            extra={
                "max_stage_iterations": settings.reflection_settings.max_stage_iterations,
                "max_cross_stage_iterations": settings.reflection_settings.max_cross_stage_iterations,
            },
        )

    # Create validation agents if enabled
    validation_registry: ValidationAgentRegistry | None = None
    if settings.validation_settings.enable_validation_agents:
        from hypoforge.agents.validation_base import ValidationAgentRegistry
        from hypoforge.agents.evidence_validator import EvidenceValidator
        from hypoforge.agents.conflict_detector import ConflictDetector
        from hypoforge.agents.quality_assessor import QualityAssessor

        validation_registry = ValidationAgentRegistry()

        # Register validators for each stage
        validation_registry.register(EvidenceValidator(
            repository=repository,
            settings=settings.validation_settings,
            provider=provider,
        ))
        validation_registry.register(ConflictDetector(
            repository=repository,
            settings=settings.validation_settings,
            provider=provider,
        ))
        validation_registry.register(QualityAssessor(
            repository=repository,
            settings=settings.validation_settings,
            provider=provider,
        ))

        logger.info(
            "Validation agents enabled",
            extra={
                "min_valid_evidence": settings.validation_settings.min_valid_evidence,
                "min_quality_score": settings.validation_settings.min_quality_score,
            },
        )

    from hypoforge.application.event_bus import RunEventBus
    event_bus = RunEventBus()

    coordinator = RunCoordinator(
        repository=repository,
        retrieval_agent=retrieval_agent,
        review_agent=review_agent,
        critic_agent=critic_agent,
        planner_agent=planner_agent,
        report_renderer=renderer,
        reflection_agent=reflection_agent,
        reflection_settings=settings.reflection_settings,
        stage_navigator=stage_navigator,
        validation_registry=validation_registry,
        validation_settings=settings.validation_settings,
        event_bus=event_bus,
    )
    return ServiceContainer(coordinator=coordinator, event_bus=event_bus)


def _summarize_tool_result(result: dict) -> dict:
    summary: dict[str, object] = {}
    if "papers" in result:
        summary["paper_count"] = len(result["papers"])
        summary["result_count"] = len(result["papers"])
        summary["paper_ids"] = [paper.get("paper_id") for paper in result["papers"][:5]]
    if "paper_content" in result:
        summary["result_count"] = 1
        summary["content_length"] = len(result["paper_content"])
    if "answer" in result:
        summary["result_count"] = 1
        summary["answer_length"] = len(result["answer"])
    if "repository_content" in result:
        summary["result_count"] = 1
        summary["content_length"] = len(str(result["repository_content"]))
    if "evidence_cards" in result:
        summary["result_count"] = len(result["evidence_cards"])
    if "evidence_ids" in result:
        summary["result_count"] = len(result["evidence_ids"])
        summary["evidence_ids"] = result["evidence_ids"][:5]
    if "cluster_ids" in result:
        summary["result_count"] = len(result["cluster_ids"])
        summary["cluster_ids"] = result["cluster_ids"][:5]
    if "hypothesis_ranks" in result:
        summary["result_count"] = len(result["hypothesis_ranks"])
        summary["hypothesis_ranks"] = result["hypothesis_ranks"]
    if "report_markdown" in result:
        summary["report_length"] = len(result["report_markdown"])
        summary["result_count"] = 1
    if "cache_hit" in result:
        summary["cache_hit"] = result["cache_hit"]
    if "error" in result:
        summary["error"] = result["error"]
    if not summary:
        summary = result
    return summary


def _lookup_candidate_papers(candidate_pool: dict[str, PaperDetail], paper_ids: list[str]) -> list[PaperDetail]:
    papers: list[PaperDetail] = []
    all_candidates = list(candidate_pool.values())
    for paper_id in paper_ids:
        candidate = candidate_pool.get(paper_id)
        if candidate is None:
            continue
        key = paper_identity_key(candidate)
        duplicates = [paper for paper in all_candidates if paper_identity_key(paper) == key]
        merged = candidate
        for duplicate in duplicates:
            if duplicate.paper_id == merged.paper_id:
                continue
            merged = merge_paper_details(merged, duplicate)
        papers.append(merged)
    return papers




def _review_papers_in_batches(
    *,
    selected_papers: list[PaperDetail],
    batch_size: int,
    review_batch: Callable[[list[PaperDetail]], ReviewSummary],
) -> ReviewSummary:
    if not selected_papers:
        return ReviewSummary(
            papers_processed=0,
            evidence_cards_created=0,
            coverage_summary="no selected papers to review",
            dominant_axes=[],
            low_confidence_paper_ids=[],
            failed_paper_ids=[],
        )

    successful_summaries: list[ReviewSummary] = []
    total_batches = ceil(len(selected_papers) / batch_size)

    for index in range(0, len(selected_papers), batch_size):
        batch = selected_papers[index : index + batch_size]
        successful_summaries.append(review_batch(batch))

    papers_processed = sum(summary.papers_processed for summary in successful_summaries)
    evidence_cards_created = sum(summary.evidence_cards_created for summary in successful_summaries)
    dominant_axes = list(
        dict.fromkeys(axis for summary in successful_summaries for axis in summary.dominant_axes)
    )
    low_confidence_paper_ids = list(
        dict.fromkeys(
            paper_id
            for summary in successful_summaries
            for paper_id in summary.low_confidence_paper_ids
        )
    )
    coverage_summary = (
        f"processed {papers_processed}/{len(selected_papers)} selected papers "
        f"across {total_batches} batches"
    )

    return ReviewSummary(
        papers_processed=papers_processed,
        evidence_cards_created=evidence_cards_created,
        coverage_summary=coverage_summary,
        dominant_axes=dominant_axes,
        low_confidence_paper_ids=low_confidence_paper_ids,
        failed_paper_ids=[],
    )






def build_fake_services(
    *,
    database_url: str = "sqlite:///./hypoforge.fake.db",
) -> ServiceContainer:
    """Re-export: delegates to :func:`hypoforge.testing.fake_services.build_fake_services`."""
    from hypoforge.testing.fake_services import build_fake_services as _impl
    return _impl(database_url=database_url)

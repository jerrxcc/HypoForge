from __future__ import annotations

import asyncio
from dataclasses import dataclass
from hashlib import sha256
import logging
from math import ceil
from time import perf_counter
from collections import defaultdict
from typing import Callable

from hypoforge.agents.prompts import prompt_for
from hypoforge.agents.reflection import ReflectionAgent
from hypoforge.agents.providers import OpenAIResponsesProvider
from hypoforge.agents.runner import AgentRunner
from hypoforge.agents.validation_base import ValidationAgentRegistry
from hypoforge.application.budget import RunBudgetTracker, ToolStepBudgetExceededError
from hypoforge.application.coordinator import RunCoordinator
from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.application.stage_graph import StageNavigator
from hypoforge.config import ReflectionSettings, Settings, ValidationSettings
from hypoforge.domain.schemas import (
    ConflictCluster,
    CriticSummary,
    EvidenceCard,
    Hypothesis,
    MinimalExperiment,
    PaperDetail,
    PlannerSummary,
    RetrievalSummary,
    ReviewSummary,
)
from hypoforge.infrastructure.connectors.openalex import OpenAlexConnector
from hypoforge.infrastructure.connectors.cached import CachedOpenAlexConnector, CachedSemanticScholarConnector
from hypoforge.infrastructure.connectors.dedupe import dedupe_papers
from hypoforge.infrastructure.connectors.ranking import rank_papers
from hypoforge.infrastructure.connectors.semantic_scholar import SemanticScholarConnector
from hypoforge.infrastructure.db.cache_repository import CacheRepository
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.render_tools import RenderTools
from hypoforge.tools.scholarly_tools import ScholarlyTools
from hypoforge.tools.workspace_tools import WorkspaceTools


@dataclass
class ServiceContainer:
    coordinator: RunCoordinator


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
    )
    renderer = ReportRenderer()
    logger = logging.getLogger(__name__)
    openalex_base = OpenAlexConnector(api_key=settings.openalex_api_key or None)
    semantic_scholar_base = SemanticScholarConnector()
    review_prompt = prompt_for("review")
    review_prompt_version = sha256(review_prompt.encode("utf-8")).hexdigest()[:12]

    def make_tool_invoker(
        run_id: str,
        agent_name: str,
        model_name: str,
        *,
        selected_paper_ids: list[str] | None = None,
        append_evidence_cards: bool = False,
    ):
        candidate_pool = candidate_pools.setdefault(run_id, {})
        budget_tracker = budget_trackers.setdefault(
            run_id,
            RunBudgetTracker(
                max_openalex_calls=settings.max_openalex_calls_per_run,
                max_semantic_scholar_calls=settings.max_s2_calls_per_run,
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
            repository=repository,
            paper_lookup=lambda paper_ids: [candidate_pool[paper_id] for paper_id in paper_ids if paper_id in candidate_pool],
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

        def invoke(tool_name: str, payload: dict, trace_context: dict):
            started_at = perf_counter()
            try:
                result = registry[tool_name](payload)
                summary = _summarize_tool_result(result)
                if trace_context.get("request_id"):
                    summary["request_id"] = trace_context["request_id"]
                repository.record_tool_trace(
                    run_id=run_id,
                    agent_name=agent_name,
                    tool_name=tool_name,
                    args=payload,
                    result_summary=summary,
                    latency_ms=max(1, int((perf_counter() - started_at) * 1000)),
                    model_name=model_name,
                    success=True,
                    input_tokens=trace_context.get("input_tokens"),
                    output_tokens=trace_context.get("output_tokens"),
                )
                return result
            except Exception as exc:
                repository.record_tool_trace(
                    run_id=run_id,
                    agent_name=agent_name,
                    tool_name=tool_name,
                    args=payload,
                    result_summary={"error": type(exc).__name__},
                    latency_ms=max(1, int((perf_counter() - started_at) * 1000)),
                    model_name=model_name,
                    success=False,
                    input_tokens=trace_context.get("input_tokens"),
                    output_tokens=trace_context.get("output_tokens"),
                    error_message=str(exc),
                )
                raise

        return invoke

    def retrieval_agent(run_id: str, topic: str, constraints) -> RetrievalSummary:
        def execute_attempt(
            attempt_constraints: RunConstraints,
            broadened: bool,
        ) -> tuple[RetrievalSummary, int]:
            runner = AgentRunner(
                provider=provider,
                tool_invoker=make_tool_invoker(run_id, "retrieval", settings.openai_model_retrieval),
                output_model=RetrievalSummary,
                agent_name="retrieval",
                model_name=settings.openai_model_retrieval,
                max_tool_steps=settings.max_tool_steps_retrieval,
                repair_output=_repair_retrieval_output,
            )
            summary = runner.execute(
                instructions=prompt_for("retrieval"),
                context={
                    "topic": topic,
                    "constraints": attempt_constraints.model_dump(),
                    "retrieval_mode": "broadened" if broadened else "default",
                },
                tool_names=[
                    "search_openalex_works",
                    "search_semantic_scholar_papers",
                    "recommend_semantic_scholar_papers",
                    "get_paper_details",
                    "save_selected_papers",
                ],
            )
            return summary, len(repository.load_selected_papers(run_id))

        summary = _run_retrieval_with_recovery(
            topic=topic,
            constraints=constraints,
            execute_attempt=execute_attempt,
            on_tool_step_budget_exceeded=lambda: _build_retrieval_budget_summary(
                topic=topic,
                constraints=constraints,
                selected_paper_ids=[paper.paper_id for paper in repository.load_selected_papers(run_id)],
            ),
        )
        return _supplement_selected_papers_from_candidates(
            repository=repository,
            run_id=run_id,
            summary=summary,
            candidate_pool=candidate_pools.get(run_id, {}),
            max_selected_papers=constraints.max_selected_papers,
        )

    def review_agent(run_id: str) -> ReviewSummary:
        selected_papers = repository.load_selected_papers(run_id)

        def review_batch(batch: list[PaperDetail]) -> ReviewSummary:
            cached_cards = _load_cached_evidence_cards_for_papers(
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
                    selected_paper_ids=[paper.paper_id for paper in batch],
                    append_evidence_cards=True,
                ),
                output_model=ReviewSummary,
                agent_name="review",
                model_name=settings.openai_model_review,
                max_tool_steps=settings.max_tool_steps_review,
                repair_output=_repair_review_output,
            )
            summary = runner.execute(
                instructions=review_prompt,
                context={"run_id": run_id, "paper_ids": [paper.paper_id for paper in batch]},
                tool_names=["load_selected_papers", "save_evidence_cards"],
            )
            _save_evidence_cards_to_cache(
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

    def critic_agent(run_id: str) -> CriticSummary:
        runner = AgentRunner(
            provider=provider,
            tool_invoker=make_tool_invoker(run_id, "critic", settings.openai_model_critic),
            output_model=CriticSummary,
            agent_name="critic",
            model_name=settings.openai_model_critic,
            max_tool_steps=settings.max_tool_steps_critic,
            repair_output=_repair_critic_output,
        )
        try:
            return runner.execute(
                instructions=prompt_for("critic"),
                context={"run_id": run_id},
                tool_names=["load_evidence_cards", "save_conflict_clusters"],
            )
        except ToolStepBudgetExceededError:
            return _build_critic_budget_summary(repository.load_conflict_clusters(run_id))

    def planner_agent(run_id: str) -> PlannerSummary:
        runner = AgentRunner(
            provider=provider,
            tool_invoker=make_tool_invoker(run_id, "planner", settings.openai_model_planner),
            output_model=PlannerSummary,
            agent_name="planner",
            model_name=settings.openai_model_planner,
            max_tool_steps=settings.max_tool_steps_planner,
            repair_output=_repair_planner_output,
        )
        try:
            return runner.execute(
                instructions=prompt_for("planner"),
                context={"run_id": run_id},
                tool_names=["load_evidence_cards", "load_conflict_clusters", "save_hypotheses", "render_markdown_report"],
            )
        except ToolStepBudgetExceededError:
            return _build_planner_budget_summary(
                run_id=run_id,
                repository=repository,
                renderer=renderer,
            )

    # Create reflection agent if enabled
    reflection_agent: ReflectionAgent | None = None
    stage_navigator: StageNavigator | None = None
    if settings.reflection_settings.enable_reflection:
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
    )
    return ServiceContainer(coordinator=coordinator)


def _summarize_tool_result(result: dict) -> dict:
    summary: dict[str, object] = {}
    if "papers" in result:
        summary["paper_count"] = len(result["papers"])
        summary["result_count"] = len(result["papers"])
        summary["paper_ids"] = [paper.get("paper_id") for paper in result["papers"][:5]]
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


def _evidence_cache_key(paper_id: str, model_name: str, prompt_version: str) -> str:
    return f"{paper_id}:{model_name}:{prompt_version}"


def _load_cached_evidence_cards_for_papers(
    *,
    papers: list[PaperDetail],
    cache_repository: CacheRepository,
    model_name: str,
    prompt_version: str,
) -> list[EvidenceCard] | None:
    if not papers:
        return None
    cards: list[EvidenceCard] = []
    for paper in papers:
        payload = cache_repository.get(
            "evidence_extraction",
            _evidence_cache_key(paper.paper_id, model_name, prompt_version),
        )
        if payload is None:
            return None
        cards.extend(EvidenceCard.model_validate(card) for card in payload["evidence_cards"])
    return cards


def _save_evidence_cards_to_cache(
    *,
    run_id: str,
    papers: list[PaperDetail],
    repository: RunRepository,
    cache_repository: CacheRepository,
    model_name: str,
    prompt_version: str,
    ttl_seconds: int,
) -> None:
    cards = repository.load_evidence_cards(run_id)
    allowed_paper_ids = {paper.paper_id for paper in papers}
    cards_by_paper: dict[str, list[EvidenceCard]] = defaultdict(list)
    for card in cards:
        if card.paper_id not in allowed_paper_ids:
            continue
        cards_by_paper[card.paper_id].append(card)
    for paper_id, paper_cards in cards_by_paper.items():
        cache_repository.set(
            "evidence_extraction",
            _evidence_cache_key(paper_id, model_name, prompt_version),
            {"evidence_cards": [card.model_dump() for card in paper_cards]},
            ttl_seconds=ttl_seconds,
        )


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
    failed_paper_ids: list[str] = []
    last_error: Exception | None = None
    budget_exceeded = False
    total_batches = ceil(len(selected_papers) / batch_size)

    for index in range(0, len(selected_papers), batch_size):
        batch = selected_papers[index : index + batch_size]
        try:
            successful_summaries.append(review_batch(batch))
        except ToolStepBudgetExceededError as exc:
            failed_paper_ids.extend(paper.paper_id for paper in selected_papers[index:])
            last_error = exc
            budget_exceeded = True
            break
        except Exception as exc:
            failed_paper_ids.extend(paper.paper_id for paper in batch)
            last_error = exc

    if not successful_summaries and last_error is not None and not budget_exceeded:
        raise last_error

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
    failed_batches = ceil(len(failed_paper_ids) / batch_size) if failed_paper_ids else 0
    coverage_summary = (
        f"processed {papers_processed}/{len(selected_papers)} selected papers "
        f"across {total_batches} batches"
    )
    if budget_exceeded:
        coverage_summary += "; tool step budget exceeded and review stopped early"
    if failed_paper_ids:
        coverage_summary += f"; {failed_batches} failed batches degraded to partial extraction"

    return ReviewSummary(
        papers_processed=papers_processed,
        evidence_cards_created=evidence_cards_created,
        coverage_summary=coverage_summary,
        dominant_axes=dominant_axes,
        low_confidence_paper_ids=low_confidence_paper_ids,
        failed_paper_ids=failed_paper_ids,
    )


async def _review_papers_in_batches_parallel(
    *,
    selected_papers: list[PaperDetail],
    batch_size: int,
    review_batch: Callable[[list[PaperDetail]], ReviewSummary],
    max_concurrent: int = 3,
) -> ReviewSummary:
    """Process papers in parallel batches for improved efficiency.

    This is an async version that processes multiple batches concurrently,
    improving throughput for large paper sets.

    Args:
        selected_papers: Papers to review
        batch_size: Number of papers per batch
        review_batch: Function to process a single batch
        max_concurrent: Maximum concurrent batch operations

    Returns:
        Combined ReviewSummary from all batches
    """
    import asyncio

    if not selected_papers:
        return ReviewSummary(
            papers_processed=0,
            evidence_cards_created=0,
            coverage_summary="no selected papers to review",
            dominant_axes=[],
            low_confidence_paper_ids=[],
            failed_paper_ids=[],
        )

    # Create batches
    batches = [
        selected_papers[i:i + batch_size]
        for i in range(0, len(selected_papers), batch_size)
    ]
    total_batches = len(batches)

    # Process batches with semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    successful_summaries: list[ReviewSummary] = []
    failed_paper_ids: list[str] = []
    errors: list[Exception] = []

    async def process_batch(batch: list[PaperDetail], batch_idx: int) -> ReviewSummary | None:
        async with semaphore:
            try:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, review_batch, batch)
            except ToolStepBudgetExceededError as exc:
                errors.append(exc)
                failed_paper_ids.extend(p.paper_id for p in batch)
                return None
            except Exception as exc:
                errors.append(exc)
                failed_paper_ids.extend(p.paper_id for p in batch)
                return None

    # Create tasks for all batches
    tasks = [process_batch(batch, i) for i, batch in enumerate(batches)]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect successful results
    for result in results:
        if isinstance(result, ReviewSummary):
            successful_summaries.append(result)
        elif isinstance(result, Exception):
            errors.append(result)

    # Check if all failed
    if not successful_summaries and errors:
        raise errors[0]

    # Aggregate results
    papers_processed = sum(s.papers_processed for s in successful_summaries)
    evidence_cards_created = sum(s.evidence_cards_created for s in successful_summaries)
    dominant_axes = list(
        dict.fromkeys(axis for s in successful_summaries for axis in s.dominant_axes)
    )
    low_confidence_paper_ids = list(
        dict.fromkeys(
            pid for s in successful_summaries for pid in s.low_confidence_paper_ids
        )
    )

    failed_batches = ceil(len(failed_paper_ids) / batch_size) if failed_paper_ids else 0
    coverage_summary = (
        f"processed {papers_processed}/{len(selected_papers)} selected papers "
        f"across {total_batches} batches (parallel)"
    )
    if failed_paper_ids:
        coverage_summary += f"; {failed_batches} failed batches degraded to partial extraction"

    return ReviewSummary(
        papers_processed=papers_processed,
        evidence_cards_created=evidence_cards_created,
        coverage_summary=coverage_summary,
        dominant_axes=dominant_axes,
        low_confidence_paper_ids=low_confidence_paper_ids,
        failed_paper_ids=failed_paper_ids,
    )


def _run_retrieval_with_recovery(
    *,
    topic: str,
    constraints: RunConstraints,
    execute_attempt: Callable[[RunConstraints, bool], tuple[RetrievalSummary, int]],
    on_tool_step_budget_exceeded: Callable[[], RetrievalSummary] | None = None,
) -> RetrievalSummary:
    minimum_threshold = min(12, constraints.max_selected_papers)
    try:
        first_summary, first_count = execute_attempt(constraints, False)
    except ToolStepBudgetExceededError:
        if on_tool_step_budget_exceeded is None:
            raise
        return on_tool_step_budget_exceeded()
    if first_count >= minimum_threshold:
        return first_summary

    broadened_constraints = constraints.model_copy(
        update={"year_from": max(2000, constraints.year_from - 5)}
    )
    try:
        second_summary, second_count = execute_attempt(broadened_constraints, True)
    except ToolStepBudgetExceededError:
        if on_tool_step_budget_exceeded is None:
            raise
        return on_tool_step_budget_exceeded()
    second_summary.search_notes.append("broadened retrieval window after low recall")
    if second_count >= minimum_threshold:
        return second_summary

    second_summary.coverage_assessment = "low"
    second_summary.needs_broader_search = True
    second_summary.search_notes.append(
        f"low evidence mode activated for '{topic}' after broadened retrieval ({second_count}/{minimum_threshold} papers)"
    )
    return second_summary


def _supplement_selected_papers_from_candidates(
    *,
    repository: RunRepository,
    run_id: str,
    summary: RetrievalSummary,
    candidate_pool: dict[str, PaperDetail],
    max_selected_papers: int,
) -> RetrievalSummary:
    minimum_threshold = min(12, max_selected_papers)
    selected_papers = repository.load_selected_papers(run_id)
    if len(selected_papers) >= minimum_threshold or not candidate_pool:
        return summary

    ranked_candidates = rank_papers(dedupe_papers(list(candidate_pool.values())))
    selected_ids = {paper.paper_id for paper in selected_papers}
    supplement = [paper for paper in ranked_candidates if paper.paper_id not in selected_ids]
    supplement = supplement[: minimum_threshold - len(selected_papers)]
    if not supplement:
        return summary

    completed_selection = selected_papers + supplement
    repository.save_selected_papers(
        run_id,
        completed_selection,
        "automatic backfill after low recall",
    )

    summary.selected_paper_ids = [paper.paper_id for paper in completed_selection]
    summary.search_notes.append(
        f"auto-supplemented selection from candidate pool to {len(completed_selection)}/{minimum_threshold} papers"
    )
    if len(completed_selection) >= minimum_threshold and summary.coverage_assessment == "low":
        summary.coverage_assessment = "medium"
        summary.needs_broader_search = False
    return summary


def _repair_retrieval_output(output: dict, context: dict) -> dict:
    selected_paper_ids = list(output.get("selected_paper_ids") or [])
    coverage = output.get("coverage_assessment")
    if coverage not in {"good", "medium", "low"}:
        if len(selected_paper_ids) >= 12:
            coverage = "good"
        elif len(selected_paper_ids) >= 6:
            coverage = "medium"
        else:
            coverage = "low"
    return {
        "canonical_topic": output.get("canonical_topic") or context.get("topic") or "",
        "query_variants_used": list(output.get("query_variants_used") or [context.get("topic") or ""]),
        "search_notes": list(output.get("search_notes") or []),
        "selected_paper_ids": selected_paper_ids,
        "excluded_paper_ids": list(output.get("excluded_paper_ids") or []),
        "coverage_assessment": coverage,
        "needs_broader_search": bool(output.get("needs_broader_search", coverage == "low")),
    }


def _repair_review_output(output: dict, context: dict) -> dict:
    del context
    return {
        "papers_processed": int(output.get("papers_processed") or 0),
        "evidence_cards_created": int(output.get("evidence_cards_created") or 0),
        "coverage_summary": output.get("coverage_summary") or "repair parse fallback",
        "dominant_axes": list(output.get("dominant_axes") or []),
        "low_confidence_paper_ids": list(output.get("low_confidence_paper_ids") or []),
        "failed_paper_ids": list(output.get("failed_paper_ids") or []),
    }


def _repair_critic_output(output: dict, context: dict) -> dict:
    del context
    return {
        "clusters_created": int(output.get("clusters_created") or 0),
        "top_axes": list(output.get("top_axes") or []),
        "critic_notes": list(output.get("critic_notes") or []),
    }


def _repair_planner_output(output: dict, context: dict) -> dict:
    del context
    repaired = {
        "hypotheses_created": output.get("hypotheses_created"),
        "report_rendered": bool(output.get("report_rendered", False)),
        "top_axes": list(output.get("top_axes") or []),
        "planner_notes": list(output.get("planner_notes") or []),
    }
    if repaired["hypotheses_created"] is None and repaired["report_rendered"]:
        repaired["hypotheses_created"] = 3
    return repaired


def _build_retrieval_budget_summary(
    *,
    topic: str,
    constraints: RunConstraints,
    selected_paper_ids: list[str],
) -> RetrievalSummary:
    count = len(selected_paper_ids)
    minimum_threshold = min(12, constraints.max_selected_papers)
    coverage = "good" if count >= minimum_threshold else "low"
    return RetrievalSummary(
        canonical_topic=topic,
        query_variants_used=[topic],
        search_notes=["retrieval tool step budget exceeded; returning best available papers"],
        selected_paper_ids=selected_paper_ids,
        excluded_paper_ids=[],
        coverage_assessment=coverage,
        needs_broader_search=count < minimum_threshold,
    )


def _build_critic_budget_summary(clusters: list[ConflictCluster]) -> CriticSummary:
    return CriticSummary(
        clusters_created=len(clusters),
        top_axes=_top_axes_from_clusters(clusters),
        critic_notes=["critic tool step budget exceeded; returning saved clusters"],
    )


def _build_planner_budget_summary(
    *,
    run_id: str,
    repository: RunRepository,
    renderer: ReportRenderer,
) -> PlannerSummary:
    hypotheses = repository.load_hypotheses(run_id)
    if len(hypotheses) != 3:
        raise ToolStepBudgetExceededError(agent_name="planner", max_steps=0)

    run_state = repository.get_run(run_id)
    if not run_state.final_report_md:
        repository.save_report_markdown(run_id, renderer.render(repository.build_final_result(run_id)))

    return PlannerSummary(
        hypotheses_created=3,
        report_rendered=True,
        top_axes=_top_axes_from_clusters(repository.load_conflict_clusters(run_id)),
        planner_notes=["planner tool step budget exceeded; returning saved hypotheses"],
    )


def _top_axes_from_clusters(clusters: list[ConflictCluster]) -> list[str]:
    return list(dict.fromkeys(cluster.topic_axis for cluster in clusters if cluster.topic_axis))


def build_fake_services(
    *,
    database_url: str = "sqlite:///./hypoforge.fake.db",
) -> ServiceContainer:
    repository = RunRepository.from_database_url(database_url)

    def retrieval_agent(run_id: str, topic: str, constraints) -> RetrievalSummary:
        del constraints
        papers = [
            PaperDetail(
                paper_id="p1",
                title=f"{topic} study",
                abstract="Metadata-grounded abstract.",
                year=2024,
                authors=["Researcher A"],
                provenance=["fake_openalex", "fake_semantic_scholar"],
            )
        ]
        repository.save_selected_papers(run_id, papers, "fake seed selection")
        repository.record_tool_trace(
            run_id=run_id,
            agent_name="retrieval",
            tool_name="search_openalex_works",
            args={"query": topic},
            result_summary={"count": 1},
            latency_ms=1,
            model_name="fake-model",
            success=True,
        )
        return RetrievalSummary(
            canonical_topic=topic,
            query_variants_used=[topic],
            search_notes=["fake retrieval"],
            selected_paper_ids=["p1"],
            excluded_paper_ids=[],
            coverage_assessment="good",
            needs_broader_search=False,
        )

    def review_agent(run_id: str) -> ReviewSummary:
        cards = [
            EvidenceCard(
                evidence_id=f"{run_id}_e1",
                paper_id="p1",
                title="Paper 1",
                claim_text="Claim 1",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="positive",
                confidence=0.9,
            ),
            EvidenceCard(
                evidence_id=f"{run_id}_e2",
                paper_id="p1",
                title="Paper 1",
                claim_text="Claim 2",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="mixed",
                confidence=0.8,
            ),
            EvidenceCard(
                evidence_id=f"{run_id}_e3",
                paper_id="p1",
                title="Paper 1",
                claim_text="Claim 3",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="negative",
                confidence=0.7,
            ),
            EvidenceCard(
                evidence_id=f"{run_id}_e4",
                paper_id="p1",
                title="Paper 1",
                claim_text="Limitation",
                system_or_material="System",
                intervention="Intervention",
                outcome="Outcome",
                direction="unclear",
                confidence=0.5,
            ),
        ]
        repository.save_evidence_cards(run_id, cards)
        repository.record_tool_trace(
            run_id=run_id,
            agent_name="review",
            tool_name="save_evidence_cards",
            args={"count": len(cards)},
            result_summary={"evidence_ids": [card.evidence_id for card in cards]},
            latency_ms=1,
            model_name="fake-model",
            success=True,
        )
        return ReviewSummary(
            papers_processed=1,
            evidence_cards_created=len(cards),
            coverage_summary="fake review complete",
            dominant_axes=["axis"],
            low_confidence_paper_ids=[],
        )

    def critic_agent(run_id: str) -> CriticSummary:
        clusters = [
            ConflictCluster(
                cluster_id=f"{run_id}_c1",
                topic_axis="axis",
                supporting_evidence_ids=[f"{run_id}_e1", f"{run_id}_e2"],
                conflicting_evidence_ids=[f"{run_id}_e3"],
                conflict_type="conditional_divergence",
                likely_explanations=["conditions differ"],
                missing_controls=["baseline"],
                critic_summary="fake conflict",
                confidence=0.6,
            )
        ]
        repository.save_conflict_clusters(run_id, clusters)
        repository.record_tool_trace(
            run_id=run_id,
            agent_name="critic",
            tool_name="save_conflict_clusters",
            args={"count": len(clusters)},
            result_summary={"cluster_ids": [cluster.cluster_id for cluster in clusters]},
            latency_ms=1,
            model_name="fake-model",
            success=True,
        )
        return CriticSummary(clusters_created=1, top_axes=["axis"], critic_notes=["fake critic complete"])

    def planner_agent(run_id: str) -> PlannerSummary:
        hypotheses = [
            Hypothesis(
                rank=rank,
                title=f"Hypothesis {rank}",
                hypothesis_statement=f"Testable statement {rank}",
                why_plausible="Grounded in fake evidence",
                why_not_obvious="Includes counterevidence",
                supporting_evidence_ids=[f"{run_id}_e1", f"{run_id}_e2", f"{run_id}_e3"],
                counterevidence_ids=[f"{run_id}_e4"],
                prediction=f"Prediction {rank}",
                minimal_experiment=MinimalExperiment(
                    system="System",
                    design=f"Design {rank}",
                    control="Control",
                    readouts=["Readout 1"],
                    success_criteria="Success",
                    failure_interpretation="Failure",
                ),
                risks=["risk"],
                novelty_score=0.7,
                feasibility_score=0.8,
                overall_score=0.75,
            )
            for rank in (1, 2, 3)
        ]
        repository.save_hypotheses(run_id, hypotheses)
        markdown = ReportRenderer().render(repository.build_final_result(run_id))
        repository.save_report_markdown(run_id, markdown)
        repository.record_tool_trace(
            run_id=run_id,
            agent_name="planner",
            tool_name="render_markdown_report",
            args={"include_appendix": True},
            result_summary={"length": len(markdown)},
            latency_ms=1,
            model_name="fake-model",
            success=True,
        )
        return PlannerSummary(hypotheses_created=3, report_rendered=True, top_axes=["axis"], planner_notes=["fake planner complete"])

    # Create reflection components for fake services (disabled by default for tests)
    reflection_settings = ReflectionSettings(enable_reflection=False)

    coordinator = RunCoordinator(
        repository=repository,
        retrieval_agent=retrieval_agent,
        review_agent=review_agent,
        critic_agent=critic_agent,
        planner_agent=planner_agent,
        reflection_settings=reflection_settings,
    )
    return ServiceContainer(coordinator=coordinator)

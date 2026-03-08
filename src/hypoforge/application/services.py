from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from hypoforge.agents.prompts import prompt_for
from hypoforge.agents.providers import OpenAIResponsesProvider
from hypoforge.agents.runner import AgentRunner
from hypoforge.application.coordinator import RunCoordinator
from hypoforge.application.report_renderer import ReportRenderer
from hypoforge.config import Settings
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
from hypoforge.infrastructure.connectors.semantic_scholar import SemanticScholarConnector
from hypoforge.infrastructure.db.repository import RunRepository
from hypoforge.tools.render_tools import RenderTools
from hypoforge.tools.scholarly_tools import ScholarlyTools
from hypoforge.tools.workspace_tools import WorkspaceTools


@dataclass
class ServiceContainer:
    coordinator: RunCoordinator


def build_default_services(settings: Settings | None = None) -> ServiceContainer:
    settings = settings or Settings()
    repository = RunRepository.from_database_url(settings.database_url)
    candidate_pools: dict[str, dict[str, PaperDetail]] = {}
    provider = OpenAIResponsesProvider(
        api_key=settings.openai_api_key or None,
        base_url=settings.openai_base_url or None,
    )
    renderer = ReportRenderer()
    openalex = OpenAlexConnector()
    semantic_scholar = SemanticScholarConnector()
    def make_tool_invoker(run_id: str, agent_name: str, model_name: str):
        candidate_pool = candidate_pools.setdefault(run_id, {})

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
        workspace_tools = WorkspaceTools(repository=repository)
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

        def invoke(tool_name: str, payload: dict):
            started_at = perf_counter()
            try:
                result = registry[tool_name](payload)
                repository.record_tool_trace(
                    run_id=run_id,
                    agent_name=agent_name,
                    tool_name=tool_name,
                    args=payload,
                    result_summary=_summarize_tool_result(result),
                    latency_ms=max(1, int((perf_counter() - started_at) * 1000)),
                    model_name=model_name,
                    success=True,
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
                    error_message=str(exc),
                )
                raise

        return invoke

    def retrieval_agent(run_id: str, topic: str, constraints) -> RetrievalSummary:
        runner = AgentRunner(
            provider=provider,
            tool_invoker=make_tool_invoker(run_id, "retrieval", settings.openai_model_retrieval),
            output_model=RetrievalSummary,
            agent_name="retrieval",
            model_name=settings.openai_model_retrieval,
            max_tool_steps=settings.max_tool_steps_retrieval,
        )
        return runner.execute(
            instructions=prompt_for("retrieval"),
            context={"topic": topic, "constraints": constraints.model_dump()},
            tool_names=[
                "search_openalex_works",
                "search_semantic_scholar_papers",
                "recommend_semantic_scholar_papers",
                "get_paper_details",
                "save_selected_papers",
            ],
        )

    def review_agent(run_id: str) -> ReviewSummary:
        runner = AgentRunner(
            provider=provider,
            tool_invoker=make_tool_invoker(run_id, "review", settings.openai_model_review),
            output_model=ReviewSummary,
            agent_name="review",
            model_name=settings.openai_model_review,
            max_tool_steps=settings.max_tool_steps_review,
        )
        return runner.execute(
            instructions=prompt_for("review"),
            context={"run_id": run_id},
            tool_names=["load_selected_papers", "save_evidence_cards"],
        )

    def critic_agent(run_id: str) -> CriticSummary:
        runner = AgentRunner(
            provider=provider,
            tool_invoker=make_tool_invoker(run_id, "critic", settings.openai_model_critic),
            output_model=CriticSummary,
            agent_name="critic",
            model_name=settings.openai_model_critic,
            max_tool_steps=settings.max_tool_steps_critic,
        )
        return runner.execute(
            instructions=prompt_for("critic"),
            context={"run_id": run_id},
            tool_names=["load_evidence_cards", "save_conflict_clusters"],
        )

    def planner_agent(run_id: str) -> PlannerSummary:
        runner = AgentRunner(
            provider=provider,
            tool_invoker=make_tool_invoker(run_id, "planner", settings.openai_model_planner),
            output_model=PlannerSummary,
            agent_name="planner",
            model_name=settings.openai_model_planner,
            max_tool_steps=settings.max_tool_steps_planner,
        )
        return runner.execute(
            instructions=prompt_for("planner"),
            context={"run_id": run_id},
            tool_names=["load_evidence_cards", "load_conflict_clusters", "save_hypotheses", "render_markdown_report"],
        )

    coordinator = RunCoordinator(
        repository=repository,
        retrieval_agent=retrieval_agent,
        review_agent=review_agent,
        critic_agent=critic_agent,
        planner_agent=planner_agent,
    )
    return ServiceContainer(coordinator=coordinator)


def _summarize_tool_result(result: dict) -> dict:
    summary: dict[str, object] = {}
    if "papers" in result:
        summary["paper_count"] = len(result["papers"])
        summary["paper_ids"] = [paper.get("paper_id") for paper in result["papers"][:5]]
    if "evidence_ids" in result:
        summary["evidence_ids"] = result["evidence_ids"][:5]
    if "cluster_ids" in result:
        summary["cluster_ids"] = result["cluster_ids"][:5]
    if "hypothesis_ranks" in result:
        summary["hypothesis_ranks"] = result["hypothesis_ranks"]
    if "report_markdown" in result:
        summary["report_length"] = len(result["report_markdown"])
    if "error" in result:
        summary["error"] = result["error"]
    if not summary:
        summary = result
    return summary


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

    coordinator = RunCoordinator(
        repository=repository,
        retrieval_agent=retrieval_agent,
        review_agent=review_agent,
        critic_agent=critic_agent,
        planner_agent=planner_agent,
    )
    return ServiceContainer(coordinator=coordinator)

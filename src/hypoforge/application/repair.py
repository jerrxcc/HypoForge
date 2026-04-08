"""Output repair functions for each pipeline stage.

Each function normalises a partially-valid dict returned by the LLM into
the shape expected by the corresponding Pydantic summary model.
"""

from __future__ import annotations


def repair_retrieval_output(output: dict, context: dict) -> dict:
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


def repair_review_output(output: dict, context: dict) -> dict:
    del context
    return {
        "papers_processed": int(output.get("papers_processed") or 0),
        "evidence_cards_created": int(output.get("evidence_cards_created") or 0),
        "coverage_summary": output.get("coverage_summary") or "repair parse fallback",
        "dominant_axes": list(output.get("dominant_axes") or []),
        "low_confidence_paper_ids": list(output.get("low_confidence_paper_ids") or []),
        "failed_paper_ids": list(output.get("failed_paper_ids") or []),
    }


def repair_critic_output(output: dict, context: dict) -> dict:
    del context
    return {
        "clusters_created": int(output.get("clusters_created") or 0),
        "top_axes": list(output.get("top_axes") or []),
        "critic_notes": list(output.get("critic_notes") or []),
    }


def repair_planner_output(output: dict, context: dict) -> dict:
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

"""
Live batch validation — replicates 2026-03-10 strict 8-topic report level.

Usage:
    ALPHAXIV_ACCESS_TOKEN="" ./.venv/bin/python scripts/run_live_batch.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from hypoforge.api.app import create_app
from hypoforge.application.services import build_default_services
from hypoforge.config import Settings


TOPICS = (
    "diffusion model preference optimization",
    "perovskite solar cell stability additives",
    "graph neural network drug-target interaction",
    "quantum error correction surface codes",
)

CONSTRAINTS: dict[str, object] = {
    "year_from": 2018,
    "year_to": 2026,
    "open_access_only": False,
    "max_selected_papers": 18,
    "novelty_weight": 0.5,
    "feasibility_weight": 0.5,
    "lab_mode": "either",
}


@dataclass
class TopicResult:
    topic: str
    run_id: str = ""
    status: str = "not_started"
    papers: int = 0
    evidence: int = 0
    clusters: int = 0
    hypotheses: int = 0
    trace_count: int = 0
    duration_s: float = 0.0
    report_chars: int = 0
    api_get_run: int = 0
    api_get_trace: int = 0
    api_get_report: int = 0
    grounding_ok: bool = False
    hypothesis_details: list[dict] = field(default_factory=list)
    error: str | None = None


def run_single_topic(tmp_dir: Path, topic: str) -> TopicResult:
    cache_key = hashlib.sha1(topic.encode()).hexdigest()[:12]
    db_path = tmp_dir / f"batch-{cache_key}.db"
    settings = Settings().model_copy(
        update={
            "database_url": f"sqlite:///{db_path}",
            "request_timeout_seconds": 180,
        }
    )
    services = build_default_services(settings)
    client = TestClient(create_app(services=services))

    t0 = time.monotonic()
    try:
        resp = client.post("/v1/runs", json={"topic": topic, "constraints": CONSTRAINTS})
        duration = time.monotonic() - t0

        if resp.status_code != 200:
            return TopicResult(
                topic=topic, status="http_error", duration_s=duration,
                error=f"POST /v1/runs returned {resp.status_code}: {resp.text[:300]}",
            )

        body = resp.json()
        run_id = body["run_id"]

        get_run = client.get(f"/v1/runs/{run_id}")
        get_trace = client.get(f"/v1/runs/{run_id}/trace")
        get_report = client.get(f"/v1/runs/{run_id}/report.md")

        run_body = get_run.json() if get_run.status_code == 200 else body
        traces = get_trace.json() if get_trace.status_code == 200 else []
        report_md = get_report.text if get_report.status_code == 200 else ""

        hypo_details = []
        for h in (run_body.get("hypotheses") or []):
            hypo_details.append({
                "rank": h.get("rank"),
                "title": h.get("title", "")[:80],
                "supporting": len(h.get("supporting_evidence_ids") or []),
                "counter": len(h.get("counterevidence_ids") or []),
                "has_experiment": bool((h.get("minimal_experiment") or {}).get("readouts")),
            })

        return TopicResult(
            topic=topic,
            run_id=run_id,
            status=run_body.get("status", "unknown"),
            papers=len(run_body.get("selected_papers") or []),
            evidence=len(run_body.get("evidence_cards") or []),
            clusters=len(run_body.get("conflict_clusters") or []),
            hypotheses=len(run_body.get("hypotheses") or []),
            trace_count=len(traces),
            duration_s=duration,
            report_chars=len(report_md),
            api_get_run=get_run.status_code,
            api_get_trace=get_trace.status_code,
            api_get_report=get_report.status_code,
            grounding_ok=_check_grounding(run_body),
            hypothesis_details=hypo_details,
        )
    except Exception as exc:
        return TopicResult(
            topic=topic, status="exception", duration_s=time.monotonic() - t0,
            error=f"{type(exc).__name__}: {exc}",
        )


def _check_grounding(run_body: dict) -> bool:
    hypotheses = run_body.get("hypotheses") or []
    if len(hypotheses) != 3:
        return False
    evidence_ids = {c.get("evidence_id") for c in (run_body.get("evidence_cards") or [])}
    for h in hypotheses:
        supporting = h.get("supporting_evidence_ids") or []
        if len(supporting) < 3:
            return False
        if not (h.get("counterevidence_ids") or h.get("limitations")):
            return False
        if not (h.get("minimal_experiment") or {}).get("readouts"):
            return False
        for eid in supporting + (h.get("counterevidence_ids") or []):
            if eid not in evidence_ids:
                return False
    return True


def generate_report(results: list[TopicResult]) -> str:
    now = datetime.now(timezone.utc).astimezone()
    ok = [r for r in results if r.status == "done"]
    fail = [r for r in results if r.status != "done"]

    lines = [
        "# Live Batch Report",
        "",
        f"Date: {now.strftime('%Y-%m-%d %H:%M %z')}",
        "",
        "## Scope",
        "- Mode: `strict-spec-grounding`",
        "- Baseline: OpenAlex + Semantic Scholar (no alphaXiv)",
        "- Execution: synchronous `POST /v1/runs` + GET run/trace/report",
        "",
        "## Constraints",
    ]
    for k, v in CONSTRAINTS.items():
        lines.append(f"- `{k}={v}`")

    lines += [
        "",
        "## Results",
        "| Topic | Run ID | Status | Papers | Evidence | Clusters | Hypo | Trace | Grounding | Duration | APIs |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for r in results:
        rid = f"`{r.run_id[:16]}…`" if r.run_id else "-"
        apis = f"{r.api_get_run}/{r.api_get_trace}/{r.api_get_report}"
        grnd = "pass" if r.grounding_ok else "FAIL"
        lines.append(
            f"| {r.topic} | {rid} | {r.status} | {r.papers} | {r.evidence} "
            f"| {r.clusters} | {r.hypotheses} | {r.trace_count} | {grnd} "
            f"| {r.duration_s:.1f}s | {apis} |"
        )

    lines += ["", "## Aggregate Summary"]
    lines.append(f"- Topics tested: `{len(results)}`")
    lines.append(f"- Successful runs: `{len(ok)}/{len(results)}`")
    lines.append(f"- Failed runs: `{len(fail)}/{len(results)}`")
    lines.append(f"- Success rate: `{len(ok)/max(len(results),1)*100:.0f}%`")

    if ok:
        avg_dur = sum(r.duration_s for r in ok) / len(ok)
        lines.append(f"- Average duration: `{avg_dur:.1f}s`")
        lines.append(f"- Paper count range: `{min(r.papers for r in ok)}-{max(r.papers for r in ok)}`")
        lines.append(f"- Evidence count range: `{min(r.evidence for r in ok)}-{max(r.evidence for r in ok)}`")
        lines.append(f"- Cluster range: `{min(r.clusters for r in ok)}-{max(r.clusters for r in ok)}`")
        lines.append(f"- Trace count range: `{min(r.trace_count for r in ok)}-{max(r.trace_count for r in ok)}`")
        lines.append(f"- All grounding checks passed: `{all(r.grounding_ok for r in ok)}`")
        lines.append(f"- All API routes 200: `{all(r.api_get_run==200 and r.api_get_trace==200 and r.api_get_report==200 for r in ok)}`")

    if fail:
        lines += ["", "## Failures"]
        for r in fail:
            lines.append(f"- **{r.topic}**: status=`{r.status}`, error=`{r.error or 'unknown'}`")

    lines += [
        "",
        "## Hypothesis Grounding Detail",
        "",
    ]
    for r in ok:
        lines.append(f"### {r.topic}")
        for h in r.hypothesis_details:
            lines.append(
                f"- H{h['rank']}: {h['title']}… "
                f"(support={h['supporting']}, counter={h['counter']}, experiment={'yes' if h['has_experiment'] else 'NO'})"
            )
        lines.append("")

    lines += [
        "## Caution",
        "- Empirical batch result, not a mathematical guarantee.",
        "- Right wording: \"the current system runs end-to-end successfully on this batch\".",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    tmp_dir = Path("/tmp/hypoforge-live-batch")
    tmp_dir.mkdir(exist_ok=True)

    print(f"Starting live batch: {len(TOPICS)} topics")
    print(f"max_selected_papers={CONSTRAINTS['max_selected_papers']}")
    print("=" * 70)

    results: list[TopicResult] = []
    for i, topic in enumerate(TOPICS, 1):
        print(f"\n[{i}/{len(TOPICS)}] {topic}")
        sys.stdout.flush()
        result = run_single_topic(tmp_dir, topic)
        results.append(result)

        icon = "PASS" if result.status == "done" and result.grounding_ok else "FAIL"
        print(
            f"  {icon} | status={result.status} | "
            f"P={result.papers} E={result.evidence} C={result.clusters} H={result.hypotheses} | "
            f"{result.duration_s:.1f}s"
        )
        if result.error:
            print(f"  ERROR: {result.error[:200]}")
        for h in result.hypothesis_details:
            print(f"    H{h['rank']}: support={h['supporting']} counter={h['counter']} exp={'Y' if h['has_experiment'] else 'N'} | {h['title']}")
        sys.stdout.flush()

    print("\n" + "=" * 70)
    ok_count = sum(1 for r in results if r.status == "done")
    print(f"Batch complete: {ok_count}/{len(results)} successful")

    report_md = generate_report(results)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = Path("docs/reports") / f"{date_str}-live-batch-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")
    print(f"Report: {report_path}")

    json_path = tmp_dir / f"{date_str}-results.json"
    json_path.write_text(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False))
    print(f"Raw JSON: {json_path}")


if __name__ == "__main__":
    main()

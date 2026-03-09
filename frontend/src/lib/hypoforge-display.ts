import type { StageName, StageStatus, StageSummary, ToolTrace } from '@/lib/hypoforge';

export type SummaryEntry = {
  label: string;
  value: string;
};

const stageDescriptions: Record<StageName, string> = {
  retrieval: 'Source expansion, dedupe, and candidate curation.',
  review: 'Evidence extraction with partial-preservation safeguards.',
  critic: 'Conflict clustering and weakness analysis.',
  planner: 'Hypothesis drafting and report rendering.'
};

const stageStateLabels: Record<StageStatus | 'pending', string> = {
  pending: 'Pending',
  started: 'In progress',
  completed: 'Completed',
  degraded: 'Degraded',
  failed: 'Failed'
};

function asCount(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function asText(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function formatListPreview(value: unknown, limit = 2): string | null {
  const items = asList(value)
    .map((item) => asText(item) ?? String(item))
    .filter(Boolean);
  if (!items.length) {
    return null;
  }
  return items.slice(0, limit).join(' • ');
}

export function getStageDescription(stageName: StageName): string {
  return stageDescriptions[stageName];
}

export function getStageStateLabel(status: StageStatus | 'pending'): string {
  return stageStateLabels[status];
}

export function getStageSummaryEntries(summary?: StageSummary): SummaryEntry[] {
  if (!summary) {
    return [];
  }

  const payload = summary.summary;

  switch (summary.stage_name) {
    case 'retrieval': {
      const selectedCount = asList(payload.selected_paper_ids).length;
      const queryCount = asList(payload.query_variants_used).length;
      const coverage = asText(payload.coverage_assessment);
      const note = formatListPreview(payload.search_notes, 1);
      return [
        { label: 'Selection', value: `${selectedCount} papers` },
        {
          label: 'Coverage',
          value: coverage ? coverage : 'not reported'
        },
        {
          label: 'Queries',
          value: `${queryCount || 1} variants`
        },
        ...(note ? [{ label: 'Note', value: note }] : [])
      ];
    }
    case 'review': {
      const processed = asCount(payload.papers_processed);
      const cards = asCount(payload.evidence_cards_created);
      const failed = asList(payload.failed_paper_ids).length;
      const axes = formatListPreview(payload.dominant_axes);
      return [
        {
          label: 'Coverage',
          value:
            processed !== null ? `${processed} papers processed` : 'not reported'
        },
        {
          label: 'Evidence',
          value: cards !== null ? `${cards} cards created` : 'not reported'
        },
        {
          label: 'Failures',
          value: failed ? `${failed} papers degraded` : 'none'
        },
        ...(axes ? [{ label: 'Axes', value: axes }] : [])
      ];
    }
    case 'critic': {
      const clusters = asCount(payload.clusters_created);
      const axes = formatListPreview(payload.top_axes);
      const note = formatListPreview(payload.critic_notes, 1);
      return [
        {
          label: 'Clusters',
          value: clusters !== null ? `${clusters} clusters` : 'not reported'
        },
        ...(axes ? [{ label: 'Top axes', value: axes }] : []),
        ...(note ? [{ label: 'Note', value: note }] : [])
      ];
    }
    case 'planner': {
      const hypotheses = asCount(payload.hypotheses_created);
      const reportRendered = payload.report_rendered === true ? 'rendered' : 'not rendered';
      const axes = formatListPreview(payload.top_axes);
      const note = formatListPreview(payload.planner_notes, 1);
      return [
        {
          label: 'Hypotheses',
          value:
            hypotheses !== null ? `${hypotheses} drafted` : 'not reported'
        },
        { label: 'Report', value: reportRendered },
        ...(axes ? [{ label: 'Top axes', value: axes }] : []),
        ...(note ? [{ label: 'Note', value: note }] : [])
      ];
    }
    default:
      return [];
  }
}

export function getTraceSummaryEntries(trace: ToolTrace): SummaryEntry[] {
  const payload = trace.result_summary;
  const resultCount = asCount(payload.result_count);
  const paperCount = asCount(payload.paper_count);
  const cacheHit = payload.cache_hit === true ? 'cache hit' : null;
  const requestId = asText(payload.request_id) ?? trace.request_id;
  const error =
    asText(trace.error_message) ||
    asText(payload.error) ||
    asText((payload.error as { message?: string } | undefined)?.message);

  return [
    ...(resultCount !== null
      ? [{ label: 'Result count', value: String(resultCount) }]
      : []),
    ...(paperCount !== null
      ? [{ label: 'Paper count', value: String(paperCount) }]
      : []),
    ...(cacheHit ? [{ label: 'Cache', value: cacheHit }] : []),
    ...(requestId ? [{ label: 'Request', value: requestId }] : []),
    ...(error ? [{ label: 'Error', value: error }] : [])
  ];
}

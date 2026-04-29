'use client';

import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { EvidenceLink } from '../evidence-link';
import { Section, BulletList, scoreVariant } from './shared';
import type { Hypothesis } from '@/types';

const SCORE_COLOR: Record<string, string> = {
  success: 'bg-success',
  warning: 'bg-warning',
  error: 'bg-destructive',
};

function ScoreBar({ label, score }: { readonly label: string; readonly score: number }) {
  const variant = scoreVariant(score);
  const pct = Math.round(score * 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 shrink-0 text-muted-foreground">{label}</span>
      <div
        role="progressbar"
        aria-label={`${label}: ${pct}%`}
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-1.5 flex-1 rounded-full bg-muted"
      >
        <div
          className={`h-full w-full origin-left rounded-full transition-transform ${SCORE_COLOR[variant]}`}
          style={{ transform: `scaleX(${pct / 100})` }}
        />
      </div>
      <span className="w-8 shrink-0 tabular-nums text-right font-medium">{score.toFixed(2)}</span>
    </div>
  );
}

interface HypothesisDetailProps {
  readonly hypothesis: Hypothesis;
}

export function HypothesisDetail({ hypothesis }: HypothesisDetailProps) {
  const { minimal_experiment: exp } = hypothesis;

  return (
    <div className="flex min-w-0 max-w-full flex-col gap-5 p-4 [overflow-wrap:anywhere]">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs">
            #{hypothesis.rank}
          </Badge>
          <h2 className="min-w-0 text-lg font-semibold leading-snug [overflow-wrap:anywhere]">{hypothesis.title}</h2>
        </div>
        <div className="flex w-full max-w-sm min-w-0 flex-col gap-1.5">
          <ScoreBar label="Novelty" score={hypothesis.novelty_score} />
          <ScoreBar label="Feasibility" score={hypothesis.feasibility_score} />
          <ScoreBar label="Overall" score={hypothesis.overall_score} />
        </div>
      </div>

      <Separator />

      {/* Hypothesis Statement */}
      <Section title="Hypothesis Statement">
        <p className="text-sm leading-relaxed">{hypothesis.hypothesis_statement}</p>
      </Section>

      {/* Why Plausible */}
      <Section title="Why Plausible">
        <p className="text-sm leading-relaxed">{hypothesis.why_plausible}</p>
      </Section>

      {/* Why Not Obvious */}
      <Section title="Why Not Obvious">
        <p className="text-sm leading-relaxed">{hypothesis.why_not_obvious}</p>
      </Section>

      <Separator />

      {/* Supporting Evidence */}
      <Section title="Supporting Evidence">
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {hypothesis.supporting_evidence_ids.length > 0
            ? hypothesis.supporting_evidence_ids.map((id) => (
                <EvidenceLink key={id} evidenceId={id} />
              ))
            : <span className="text-sm text-muted-foreground">None</span>}
        </div>
      </Section>

      {/* Counter Evidence */}
      <Section title="Counter Evidence">
        <div className="flex min-w-0 flex-wrap gap-1.5">
          {hypothesis.counterevidence_ids.length > 0
            ? hypothesis.counterevidence_ids.map((id) => (
                <EvidenceLink key={id} evidenceId={id} variant="counter" />
              ))
            : <span className="text-sm text-muted-foreground">None</span>}
        </div>
      </Section>

      <Separator />

      {/* Prediction */}
      <Section title="Prediction">
        <div className="rounded-lg border bg-muted/30 p-3">
          <p className="text-sm leading-relaxed">{hypothesis.prediction}</p>
        </div>
      </Section>

      {/* Minimal Experiment */}
      <Section title="Minimal Experiment">
        <div className="rounded-lg border bg-muted/30 p-3 space-y-2">
          <div>
            <span className="text-xs font-medium text-muted-foreground">System:</span>
            <p className="text-sm">{exp.system}</p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground">Design:</span>
            <p className="text-sm">{exp.design}</p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground">Control:</span>
            <p className="text-sm">{exp.control}</p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground">Readouts:</span>
            <ul className="list-disc pl-4 text-sm">
              {exp.readouts.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground">Success Criteria:</span>
            <p className="text-sm">{exp.success_criteria}</p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground">Failure Interpretation:</span>
            <p className="text-sm">{exp.failure_interpretation}</p>
          </div>
        </div>
      </Section>

      <Separator />

      {/* Limitations, Uncertainty, Risks */}
      <Section title="Limitations">
        <BulletList items={hypothesis.limitations} />
      </Section>

      <Section title="Uncertainty Notes">
        <BulletList items={hypothesis.uncertainty_notes} />
      </Section>

      <Section title="Risks">
        <BulletList items={hypothesis.risks} />
      </Section>
    </div>
  );
}

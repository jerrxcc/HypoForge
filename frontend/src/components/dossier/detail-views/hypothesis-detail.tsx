'use client';

import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useDossierStore } from '@/stores/dossier-store';
import { EvidenceLink } from '../evidence-link';
import type { Hypothesis } from '@/types';

function CounterEvidenceLink({ evidenceId }: { readonly evidenceId: string }) {
  const select = useDossierStore((s) => s.select);
  const expandGroup = useDossierStore((s) => s.expandGroup);

  return (
    <Badge
      variant="outline"
      className="cursor-pointer font-mono text-xs border-destructive/40 text-destructive hover:bg-destructive/10 transition-colors"
      onClick={() => {
        expandGroup('evidence');
        select('evidence', evidenceId);
      }}
    >
      {evidenceId}
    </Badge>
  );
}

function ScoreBadge({ label, score }: { readonly label: string; readonly score: number }) {
  const variant = score >= 0.7 ? 'success' : score >= 0.4 ? 'warning' : 'error';
  return (
    <Badge variant={variant as 'success' | 'warning' | 'error'} className="text-xs">
      {label}: {score.toFixed(2)}
    </Badge>
  );
}

function Section({ title, children }: { readonly title: string; readonly children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
      {children}
    </div>
  );
}

function BulletList({ items }: { readonly items: readonly string[] }) {
  if (items.length === 0) return <p className="text-sm text-muted-foreground">None</p>;
  return (
    <ul className="list-disc pl-4 text-sm space-y-1">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

interface HypothesisDetailProps {
  readonly hypothesis: Hypothesis;
}

export function HypothesisDetail({ hypothesis }: HypothesisDetailProps) {
  const { minimal_experiment: exp } = hypothesis;

  return (
    <div className="flex flex-col gap-5 p-4">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs">
            #{hypothesis.rank}
          </Badge>
          <h3 className="text-lg font-semibold">{hypothesis.title}</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <ScoreBadge label="Novelty" score={hypothesis.novelty_score} />
          <ScoreBadge label="Feasibility" score={hypothesis.feasibility_score} />
          <ScoreBadge label="Overall" score={hypothesis.overall_score} />
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
        <div className="flex flex-wrap gap-1.5">
          {hypothesis.supporting_evidence_ids.length > 0
            ? hypothesis.supporting_evidence_ids.map((id) => (
                <EvidenceLink key={id} evidenceId={id} />
              ))
            : <span className="text-sm text-muted-foreground">None</span>}
        </div>
      </Section>

      {/* Counter Evidence */}
      <Section title="Counter Evidence">
        <div className="flex flex-wrap gap-1.5">
          {hypothesis.counterevidence_ids.length > 0
            ? hypothesis.counterevidence_ids.map((id) => (
                <CounterEvidenceLink key={id} evidenceId={id} />
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

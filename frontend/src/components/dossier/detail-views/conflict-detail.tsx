'use client';

import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { EvidenceLink } from '../evidence-link';
import type { ConflictCluster } from '@/types';

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

const CONFLICT_TYPE_LABEL: Record<string, string> = {
  direct_conflict: 'Direct Conflict',
  conditional_divergence: 'Conditional Divergence',
  weak_evidence_gap: 'Weak Evidence Gap',
};

interface ConflictDetailProps {
  readonly conflict: ConflictCluster;
}

export function ConflictDetail({ conflict }: ConflictDetailProps) {
  return (
    <div className="flex flex-col gap-5 p-4">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-semibold">{conflict.topic_axis}</h3>
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">
            {CONFLICT_TYPE_LABEL[conflict.conflict_type] ?? conflict.conflict_type}
          </Badge>
          <Badge variant="secondary" className="text-xs">
            Confidence: {conflict.confidence.toFixed(2)}
          </Badge>
        </div>
      </div>

      <Separator />

      {/* Two-column evidence grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Section title="Supporting Evidence">
          <div className="flex flex-wrap gap-1.5">
            {conflict.supporting_evidence_ids.length > 0
              ? conflict.supporting_evidence_ids.map((id) => (
                  <EvidenceLink key={id} evidenceId={id} />
                ))
              : <span className="text-sm text-muted-foreground">None</span>}
          </div>
        </Section>

        <Section title="Conflicting Evidence">
          <div className="flex flex-wrap gap-1.5">
            {conflict.conflicting_evidence_ids.length > 0
              ? conflict.conflicting_evidence_ids.map((id) => (
                  <EvidenceLink key={id} evidenceId={id} />
                ))
              : <span className="text-sm text-muted-foreground">None</span>}
          </div>
        </Section>
      </div>

      <Separator />

      <Section title="Likely Explanations">
        <BulletList items={conflict.likely_explanations} />
      </Section>

      <Section title="Missing Controls">
        <BulletList items={conflict.missing_controls} />
      </Section>

      <Separator />

      <Section title="Critic Summary">
        <p className="text-sm leading-relaxed">{conflict.critic_summary}</p>
      </Section>
    </div>
  );
}

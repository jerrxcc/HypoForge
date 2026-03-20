'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { PaperLink } from '../evidence-link';
import { cn } from '@/lib/utils';
import type { EvidenceCard, Direction } from '@/types';

function directionVariant(direction: Direction): 'success' | 'error' | 'warning' | 'secondary' {
  switch (direction) {
    case 'positive':
      return 'success';
    case 'negative':
      return 'error';
    case 'mixed':
      return 'warning';
    case 'null':
    case 'unclear':
    default:
      return 'secondary';
  }
}

function Section({ title, children }: { readonly title: string; readonly children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
      {children}
    </div>
  );
}

function FieldRow({ label, value }: { readonly label: string; readonly value: string }) {
  if (!value) return null;
  return (
    <div className="flex gap-2 text-sm">
      <span className="shrink-0 font-medium text-muted-foreground">{label}:</span>
      <span>{value}</span>
    </div>
  );
}

interface EvidenceDetailProps {
  readonly evidence: EvidenceCard;
}

export function EvidenceDetail({ evidence }: EvidenceDetailProps) {
  const [groundingOpen, setGroundingOpen] = useState(false);

  return (
    <div className="flex flex-col gap-5 p-4">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-semibold">{evidence.title}</h3>
        <div className="flex flex-wrap gap-2">
          <Badge variant={directionVariant(evidence.direction)}>
            {evidence.direction}
          </Badge>
          <Badge variant="outline">{evidence.evidence_kind}</Badge>
          <Badge variant="secondary" className="text-xs">
            Confidence: {evidence.confidence.toFixed(2)}
          </Badge>
        </div>
      </div>

      <Separator />

      {/* Claim */}
      <Section title="Claim">
        <p className="text-sm leading-relaxed">{evidence.claim_text}</p>
      </Section>

      <Separator />

      {/* PICO Fields */}
      <Section title="PICO">
        <div className="space-y-1">
          <FieldRow label="System/Material" value={evidence.system_or_material} />
          <FieldRow label="Intervention" value={evidence.intervention} />
          <FieldRow label="Comparator" value={evidence.comparator} />
          <FieldRow label="Outcome" value={evidence.outcome} />
        </div>
      </Section>

      <Separator />

      {/* Paper */}
      <Section title="Paper">
        <PaperLink paperId={evidence.paper_id} />
      </Section>

      {/* Conditions */}
      {evidence.conditions.length > 0 && (
        <Section title="Conditions">
          <div className="flex flex-wrap gap-1.5">
            {evidence.conditions.map((c, i) => (
              <Badge key={i} variant="secondary" className="text-xs">
                {c}
              </Badge>
            ))}
          </div>
        </Section>
      )}

      {/* Limitations */}
      {evidence.limitations.length > 0 && (
        <Section title="Limitations">
          <ul className="list-disc pl-4 text-sm space-y-1">
            {evidence.limitations.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Grounding Notes */}
      {evidence.grounding_notes.length > 0 && (
        <>
          <Separator />
          <div>
            <button
              type="button"
              onClick={() => setGroundingOpen((prev) => !prev)}
              className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronDown
                className={cn(
                  'size-4 transition-transform duration-200',
                  groundingOpen && 'rotate-180',
                )}
              />
              Grounding Notes
            </button>
            {groundingOpen && (
              <ul className="mt-2 list-disc pl-4 text-sm space-y-1">
                {evidence.grounding_notes.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}

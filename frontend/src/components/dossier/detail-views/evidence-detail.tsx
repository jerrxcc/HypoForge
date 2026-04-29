'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { PaperLink } from '../evidence-link';
import { cn } from '@/lib/utils';
import { Section, directionVariant } from './shared';
import type { EvidenceCard } from '@/types';

function FieldRow({ label, value }: { readonly label: string; readonly value: string }) {
  if (!value) return null;
  return (
    <div className="flex min-w-0 gap-2 text-sm">
      <span className="shrink-0 font-medium text-muted-foreground">{label}:</span>
      <span className="min-w-0 [overflow-wrap:anywhere]">{value}</span>
    </div>
  );
}

interface EvidenceDetailProps {
  readonly evidence: EvidenceCard;
}

export function EvidenceDetail({ evidence }: EvidenceDetailProps) {
  const [groundingOpen, setGroundingOpen] = useState(false);
  const groundingId = `grounding-notes-${evidence.evidence_id}`;

  return (
    <div className="flex min-w-0 max-w-full flex-col gap-5 p-4 [overflow-wrap:anywhere]">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h2 className="min-w-0 text-lg font-semibold leading-snug [overflow-wrap:anywhere]">{evidence.title}</h2>
        <div className="flex min-w-0 flex-wrap gap-2">
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
        <div className="min-w-0 space-y-1">
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
          <div className="flex min-w-0 flex-wrap gap-1.5">
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
          <ul className="list-disc pl-4 text-sm space-y-1 [overflow-wrap:anywhere]">
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
              aria-expanded={groundingOpen}
              aria-controls={groundingId}
              className="flex items-center gap-1.5 rounded text-sm font-medium text-muted-foreground hover:text-foreground transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
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
              <ul id={groundingId} className="mt-2 list-disc pl-4 text-sm space-y-1 [overflow-wrap:anywhere]">
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

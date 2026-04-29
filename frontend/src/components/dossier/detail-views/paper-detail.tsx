'use client';

import { ExternalLink } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Section } from './shared';
import type { PaperDetail as PaperDetailType } from '@/types';

interface PaperDetailProps {
  readonly paper: PaperDetailType;
}

export function PaperDetailView({ paper }: PaperDetailProps) {
  return (
    <div className="flex min-w-0 max-w-full flex-col gap-5 p-4 [overflow-wrap:anywhere]">
      {/* Title */}
      <h2 className="min-w-0 text-lg font-semibold leading-snug [overflow-wrap:anywhere]">{paper.title}</h2>

      {/* Metadata row */}
      <div className="flex min-w-0 flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
        {paper.authors.length > 0 && (
          <span>{paper.authors.join(', ')}</span>
        )}
        {paper.year && <span>{paper.year}</span>}
        {paper.venue && <span>{paper.venue}</span>}
        {paper.citation_count != null && (
          <span>{paper.citation_count} citations</span>
        )}
      </div>

      <Separator />

      {/* Abstract */}
      <Section title="Abstract">
        <p className="text-sm leading-relaxed">
          {paper.abstract ?? 'No abstract available'}
        </p>
      </Section>

      {/* Fields of study */}
      {paper.fields_of_study.length > 0 && (
        <Section title="Fields of Study">
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {paper.fields_of_study.map((field, i) => (
              <Badge key={i} variant="secondary" className="text-xs">
                {field}
              </Badge>
            ))}
          </div>
        </Section>
      )}

      <Separator />

      {/* Links */}
      <Section title="Links">
        <div className="flex min-w-0 flex-wrap gap-2">
          {paper.doi && (
            <a
              href={`https://doi.org/${paper.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              DOI <ExternalLink aria-hidden="true" className="size-3" />
              <span className="sr-only">(opens in new tab)</span>
            </a>
          )}
          {paper.url && (
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              Source <ExternalLink aria-hidden="true" className="size-3" />
              <span className="sr-only">(opens in new tab)</span>
            </a>
          )}
          {Object.entries(paper.source_urls).map(([name, url]) => (
            <a
              key={name}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              {name} <ExternalLink aria-hidden="true" className="size-3" />
              <span className="sr-only">(opens in new tab)</span>
            </a>
          ))}
        </div>
        {!paper.doi && !paper.url && Object.keys(paper.source_urls).length === 0 && (
          <p className="text-sm text-muted-foreground">No links available</p>
        )}
      </Section>

      {/* Provenance */}
      {paper.provenance.length > 0 && (
        <Section title="Provenance">
          <ul className="list-disc pl-4 text-sm space-y-1 [overflow-wrap:anywhere]">
            {paper.provenance.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

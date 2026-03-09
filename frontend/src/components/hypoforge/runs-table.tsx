'use client';

import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

import { RunStatusBadge } from '@/components/hypoforge/run-status-badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import type { RunSummary } from '@/lib/hypoforge';

function compactError(errorMessage: string | null): string | null {
  if (!errorMessage) {
    return null;
  }
  const compact = errorMessage.replace(/\s+/g, ' ').trim();
  return compact.length > 140 ? `${compact.slice(0, 137)}...` : compact;
}

function RunCard({ run }: { run: RunSummary }) {
  const errorPreview = compactError(run.error_message);

  return (
    <Link
      href={`/dashboard/runs/${run.run_id}`}
      className='block rounded-[1.65rem] border border-border/70 bg-card/90 p-5 shadow-sm transition-transform hover:-translate-y-0.5'
    >
      <div className='flex items-start justify-between gap-3'>
        <div className='min-w-0 space-y-2'>
          <div className='text-muted-foreground text-[11px] uppercase tracking-[0.18em]'>
            Run dossier
          </div>
          <div className='line-clamp-2 font-serif text-2xl leading-tight'>
            {run.topic}
          </div>
          <div className='text-muted-foreground break-all font-mono text-[12px]'>
            {run.run_id}
          </div>
        </div>
        <RunStatusBadge status={run.status} />
      </div>

      <div className='mt-5 grid grid-cols-3 gap-3'>
        {[
          ['Papers', run.selected_paper_count],
          ['Evidence', run.evidence_card_count],
          ['Hypotheses', run.hypothesis_count]
        ].map(([label, value]) => (
          <div
            key={label}
            className='rounded-2xl border border-border/70 bg-background/80 px-3 py-3'
          >
            <div className='text-muted-foreground text-[11px] uppercase tracking-[0.16em]'>
              {label}
            </div>
            <div className='mt-2 font-serif text-2xl'>{value}</div>
          </div>
        ))}
      </div>

      <div className='mt-4 flex flex-wrap items-center gap-2 text-sm text-muted-foreground'>
        <span>Updated {formatDistanceToNow(new Date(run.updated_at), { addSuffix: true })}</span>
        {errorPreview ? (
          <span className='line-clamp-2 rounded-2xl border border-destructive/20 bg-destructive/10 px-3 py-2 text-destructive'>
            {errorPreview}
          </span>
        ) : null}
      </div>
    </Link>
  );
}

export function RunsTable({ runs }: { runs: RunSummary[] }) {
  if (!runs.length) {
    return (
      <div className='rounded-[1.8rem] border border-dashed border-border/80 bg-background/75 px-6 py-12 text-center'>
        <div className='font-serif text-3xl'>No runs yet.</div>
        <p className='text-muted-foreground mx-auto mt-3 max-w-xl text-sm leading-7'>
          Start a topic from the new-run workspace to create your first dossier, then
          come back here to audit progress, trace history, and final reports.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className='grid gap-4 xl:hidden'>
        {runs.map((run) => (
          <RunCard key={run.run_id} run={run} />
        ))}
      </div>

      <div className='hidden xl:block'>
        <Table className='table-fixed'>
          <TableHeader>
            <TableRow className='border-border/80'>
              <TableHead className='w-[42%]'>Topic</TableHead>
              <TableHead className='w-[14%]'>Status</TableHead>
              <TableHead className='w-[16%]'>Updated</TableHead>
              <TableHead className='text-right'>Papers</TableHead>
              <TableHead className='text-right'>Evidence</TableHead>
              <TableHead className='text-right'>Hypotheses</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runs.map((run) => (
              <TableRow key={run.run_id} className='border-border/70 align-top'>
                <TableCell className='whitespace-normal pr-4'>
                  <Link
                    href={`/dashboard/runs/${run.run_id}`}
                    className='block rounded-2xl border border-transparent px-2 py-1 -mx-2 transition-colors hover:border-border/60 hover:bg-background/80'
                  >
                    <div className='line-clamp-2 font-medium leading-6'>{run.topic}</div>
                    <div className='text-muted-foreground mt-2 break-all font-mono text-[12px]'>
                      {run.run_id}
                    </div>
                    {compactError(run.error_message) ? (
                      <div className='mt-3 inline-flex max-w-full rounded-2xl border border-destructive/20 bg-destructive/10 px-3 py-2 text-[11px] leading-5 text-destructive line-clamp-2'>
                        {compactError(run.error_message)}
                      </div>
                    ) : null}
                  </Link>
                </TableCell>
                <TableCell className='whitespace-normal'>
                  <RunStatusBadge status={run.status} />
                </TableCell>
                <TableCell className='text-muted-foreground whitespace-normal text-sm leading-6'>
                  {formatDistanceToNow(new Date(run.updated_at), { addSuffix: true })}
                </TableCell>
                <TableCell className='text-right font-mono text-[15px]'>
                  {run.selected_paper_count}
                </TableCell>
                <TableCell className='text-right font-mono text-[15px]'>
                  {run.evidence_card_count}
                </TableCell>
                <TableCell className='text-right font-mono text-[15px]'>
                  {run.hypothesis_count}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </>
  );
}

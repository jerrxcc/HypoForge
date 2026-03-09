'use client';

import { RunsTable } from '@/components/hypoforge/runs-table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useRuns } from '@/hooks/use-hypoforge';

export default function RunsPage() {
  const { data: runs, error, isLoading } = useRuns();

  return (
    <div className='flex flex-1 flex-col gap-6 p-4 md:p-8'>
      <Card className='border-border/70 bg-card/95 shadow-sm'>
        <CardHeader>
          <div className='text-muted-foreground text-xs uppercase tracking-[0.24em]'>
            Run archive
          </div>
          <CardTitle className='font-serif text-4xl tracking-tight'>
            Audit recent runs without losing the dossier.
          </CardTitle>
          <CardDescription className='text-base leading-relaxed'>
            Each row keeps the status, volume, and path into the full evidence trail.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading && !runs ? (
            <div className='text-muted-foreground text-sm'>Loading runs…</div>
          ) : null}
          {error ? <div className='text-sm text-destructive'>{error}</div> : null}
          {runs ? <RunsTable runs={runs} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}

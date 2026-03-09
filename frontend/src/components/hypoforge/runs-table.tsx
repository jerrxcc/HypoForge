import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

import { RunStatusBadge } from '@/components/hypoforge/run-status-badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { RunSummary } from '@/lib/hypoforge';

export function RunsTable({ runs }: { runs: RunSummary[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Topic</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Updated</TableHead>
          <TableHead>Papers</TableHead>
          <TableHead>Evidence</TableHead>
          <TableHead>Hypotheses</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {runs.map((run) => (
          <TableRow key={run.run_id}>
            <TableCell className='max-w-xl'>
              <Link
                href={`/dashboard/runs/${run.run_id}`}
                className='font-medium underline-offset-4 hover:underline'
              >
                {run.topic}
              </Link>
              <div className='text-muted-foreground mt-1 text-xs'>{run.run_id}</div>
            </TableCell>
            <TableCell>
              <RunStatusBadge status={run.status} />
            </TableCell>
            <TableCell className='text-muted-foreground text-sm'>
              {formatDistanceToNow(new Date(run.updated_at), { addSuffix: true })}
            </TableCell>
            <TableCell>{run.selected_paper_count}</TableCell>
            <TableCell>{run.evidence_card_count}</TableCell>
            <TableCell>{run.hypothesis_count}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

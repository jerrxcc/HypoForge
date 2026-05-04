'use client';

import { use } from 'react';
import Link from 'next/link';
import { useReport } from '@/hooks/use-report';
import { usePollRun } from '@/hooks/use-poll-run';
import { MarkdownRenderer } from '@/components/report/markdown-renderer';
import { DownloadButton } from '@/components/report/download-button';
import { Skeleton } from '@/components/ui/skeleton';

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: run } = usePollRun(id);
  const { data: content, isLoading } = useReport(id, run?.status);

  const topic = run?.topic ?? id;
  const filename = `${topic.toLowerCase().replace(/\s+/g, '-')}-report.md`;

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-muted-foreground">
        <ol className="flex items-center gap-1.5">
          <li><Link href="/dashboard/runs" className="hover:text-foreground transition-colors">Runs</Link></li>
          <li aria-hidden="true">/</li>
          <li><Link href={`/dashboard/runs/${id}`} className="hover:text-foreground transition-colors truncate max-w-xs">{topic}</Link></li>
          <li aria-hidden="true">/</li>
          <li aria-current="page">Report</li>
        </ol>
      </nav>

      {/* Header row */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{topic}</h1>
        {content && <DownloadButton content={content} filename={filename} />}
      </div>

      {/* Content area */}
      {isLoading ? (
        <ReportSkeleton />
      ) : content ? (
        <div className="flex-1 min-h-0 rounded-lg border border-border overflow-hidden">
          <MarkdownRenderer content={content} />
        </div>
      ) : (
        <div className="flex flex-1 items-center justify-center py-24 text-center">
          <p className="text-muted-foreground">
            Report will be available when the run completes.
          </p>
        </div>
      )}
    </div>
  );
}

function ReportSkeleton() {
  return (
    <div className="flex flex-col gap-4 p-6">
      <Skeleton className="h-7 w-2/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-4/5" />
      <Skeleton className="h-6 w-1/3 mt-4" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-full" />
    </div>
  );
}

'use client';

import React from 'react';
import { TracePanel } from '@/components/trace/trace-panel';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/primitives';

interface TracePageProps {
  params: Promise<{ id: string }>;
}

export default function TracePage({ params }: TracePageProps) {
  return <TracePageContent params={params} />;
}

function TracePageContent({ params }: { params: Promise<{ id: string }> }) {
  // For Next.js 16, params needs to be awaited
  const [resolvedParams, setResolvedParams] = React.useState<{ id: string } | null>(null);

  React.useEffect(() => {
    params.then(setResolvedParams);
  }, [params]);

  if (!resolvedParams) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/dashboard/runs/${resolvedParams.id}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Run
          </Button>
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tool Trace Inspector</h1>
        <p className="mt-1 text-gray-500">
          Inspect all tool calls made during this run.
        </p>
      </div>

      <TracePanel runId={resolvedParams.id} />
    </div>
  );
}

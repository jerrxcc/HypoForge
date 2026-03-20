'use client';

import { useState } from 'react';
import { useTrace } from '@/hooks/use-trace';
import { Loader2, Terminal } from 'lucide-react';
import { Card, Badge, ScrollArea } from '@/components/primitives';
import { formatDuration } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface TracePanelProps {
  runId: string;
}

type TraceItem = NonNullable<ReturnType<typeof useTrace>['data']>[number];

export function TracePanel({ runId }: TracePanelProps) {
  const { data: traces, isLoading, error } = useTrace(runId);
  const [selectedTrace, setSelectedTrace] = useState<TraceItem | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-700">
        Failed to load trace: {error.message}
      </div>
    );
  }

  if (!traces || traces.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <Terminal className="mx-auto h-12 w-12 text-gray-300" />
        <p className="mt-2 text-gray-500">No trace data available.</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {/* Trace list */}
      <div className="lg:col-span-1">
        <Card className="overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50 px-4 py-2">
            <h4 className="text-sm font-medium text-gray-700">Tool Calls ({traces.length})</h4>
          </div>
          <ScrollArea className="h-[600px]">
            <div className="divide-y divide-gray-100">
              {traces.map((trace) => (
                <button
                  key={trace.id}
                  onClick={() => setSelectedTrace(trace)}
                  className={cn(
                    'w-full px-4 py-3 text-left transition-colors hover:bg-gray-50',
                    selectedTrace?.id === trace.id && 'bg-blue-50'
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant={trace.success ? 'success' : 'error'} className="text-xs">
                          {trace.agent_name}
                        </Badge>
                        <span className="text-xs text-gray-400">
                          {formatDuration(trace.latency_ms)}
                        </span>
                      </div>
                      <p className="mt-1 truncate text-sm font-medium text-gray-900">
                        {trace.tool_name}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </ScrollArea>
        </Card>
      </div>

      {/* Detail inspector */}
      <div className="lg:col-span-2">
        <Card className="overflow-hidden">
          {selectedTrace ? (
            <>
              <div className="border-b border-gray-200 bg-gray-50 px-4 py-2">
                <h4 className="text-sm font-medium text-gray-700">{selectedTrace.tool_name}</h4>
              </div>
              <ScrollArea className="h-[600px] p-4">
                <div className="space-y-4">
                  {/* Meta */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Model:</span>
                      <span className="ml-2 font-mono text-gray-900">{selectedTrace.model_name}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Latency:</span>
                      <span className="ml-2 text-gray-900">{formatDuration(selectedTrace.latency_ms)}</span>
                    </div>
                    {selectedTrace.input_tokens && (
                      <div>
                        <span className="text-gray-500">Input tokens:</span>
                        <span className="ml-2 text-gray-900">{selectedTrace.input_tokens}</span>
                      </div>
                    )}
                    {selectedTrace.output_tokens && (
                      <div>
                        <span className="text-gray-500">Output tokens:</span>
                        <span className="ml-2 text-gray-900">{selectedTrace.output_tokens}</span>
                      </div>
                    )}
                  </div>

                  {/* Args */}
                  <div>
                    <h5 className="mb-2 text-sm font-medium text-gray-700">Arguments</h5>
                    <pre className="overflow-x-auto rounded-lg bg-gray-900 p-3 text-xs text-gray-100">
                      {JSON.stringify(selectedTrace.args, null, 2)}
                    </pre>
                  </div>

                  {/* Result */}
                  <div>
                    <h5 className="mb-2 text-sm font-medium text-gray-700">Result</h5>
                    <pre className="overflow-x-auto rounded-lg bg-gray-900 p-3 text-xs text-gray-100">
                      {JSON.stringify(selectedTrace.result_summary, null, 2)}
                    </pre>
                  </div>

                  {/* Error */}
                  {selectedTrace.error_message && (
                    <div>
                      <h5 className="mb-2 text-sm font-medium text-rose-700">Error</h5>
                      <pre className="overflow-x-auto rounded-lg bg-rose-50 p-3 text-xs text-rose-700">
                        {selectedTrace.error_message}
                      </pre>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </>
          ) : (
            <div className="flex h-[600px] items-center justify-center text-gray-500">
              Select a tool call to view details
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

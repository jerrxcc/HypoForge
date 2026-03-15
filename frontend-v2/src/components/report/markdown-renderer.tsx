'use client';

import ReactMarkdown from 'react-markdown';
import { useReport } from '@/hooks/use-report';
import { Loader2, FileText, Download } from 'lucide-react';
import { Card, ScrollArea, Button } from '@/components/primitives';

interface MarkdownRendererProps {
  runId: string;
}

export function MarkdownRenderer({ runId }: MarkdownRendererProps) {
  const { data: markdown, isLoading, error } = useReport(runId);

  const handleDownload = () => {
    if (!markdown) return;
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hypoforge-report-${runId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

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
        Failed to load report: {error.message}
      </div>
    );
  }

  if (!markdown) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <FileText className="mx-auto h-12 w-12 text-gray-300" />
        <p className="mt-2 text-gray-500">No report generated yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Research Report</h3>
        <Button variant="outline" size="sm" onClick={handleDownload}>
          <Download className="mr-2 h-4 w-4" />
          Download MD
        </Button>
      </div>

      <Card className="overflow-hidden">
        <ScrollArea className="h-[700px]">
          <div className="prose prose-sm max-w-none p-6">
            <ReactMarkdown>{markdown}</ReactMarkdown>
          </div>
        </ScrollArea>
      </Card>
    </div>
  );
}

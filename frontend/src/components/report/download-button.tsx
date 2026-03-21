'use client';

import { useCallback } from 'react';
import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface DownloadButtonProps {
  readonly content: string;
  readonly filename?: string;
}

export function DownloadButton({ content, filename = 'report.md' }: DownloadButtonProps) {
  const handleDownload = useCallback(() => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [content, filename]);

  return (
    <Button variant="outline" size="sm" onClick={handleDownload}>
      <Download aria-hidden="true" className="size-4 mr-1.5" />
      Download
    </Button>
  );
}

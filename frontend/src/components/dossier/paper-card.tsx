'use client';

import { ExternalLink, FileText } from 'lucide-react';
import { Card } from '@/components/primitives';
import { truncate } from '@/lib/utils';
import type { PaperDetail } from '@/types';

interface PaperCardProps {
  paper: PaperDetail;
  onClick?: () => void;
}

export function PaperCard({ paper, onClick }: PaperCardProps) {
  return (
    <Card
      className="cursor-pointer p-4 transition-shadow hover:shadow-md"
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50">
          <FileText className="h-5 w-5 text-blue-600" />
        </div>
        <div className="min-w-0 flex-1">
          <h4 className="font-medium text-gray-900 line-clamp-2">
            {paper.title}
          </h4>
          <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
            {paper.year && <span>{paper.year}</span>}
            {paper.venue && (
              <>
                <span>·</span>
                <span className="truncate">{paper.venue}</span>
              </>
            )}
          </div>
          {paper.authors.length > 0 && (
            <p className="mt-1 text-xs text-gray-400 truncate">
              {paper.authors.slice(0, 3).join(', ')}
              {paper.authors.length > 3 && ' et al.'}
            </p>
          )}
          {paper.abstract && (
            <p className="mt-2 text-sm text-gray-600 line-clamp-2">
              {truncate(paper.abstract, 150)}
            </p>
          )}
        </div>
      </div>
      {paper.url && (
        <div className="mt-3 flex justify-end">
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
          >
            <ExternalLink className="h-3 w-3" />
            View paper
          </a>
        </div>
      )}
    </Card>
  );
}

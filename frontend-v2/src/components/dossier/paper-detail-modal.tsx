'use client';

import { ExternalLink, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  Badge,
} from '@/components/primitives';
import type { PaperDetail } from '@/types';

interface PaperDetailModalProps {
  paper: PaperDetail | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function PaperDetailModal({ paper, open, onOpenChange }: PaperDetailModalProps) {
  if (!paper) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-lg">{paper.title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Meta info */}
          <div className="flex flex-wrap gap-2">
            {paper.year && <Badge variant="secondary">{paper.year}</Badge>}
            {paper.source && <Badge variant="outline">{paper.source}</Badge>}
            {paper.publication_type && <Badge variant="outline">{paper.publication_type}</Badge>}
          </div>

          {/* Authors */}
          {paper.authors.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-1">Authors</h4>
              <p className="text-sm text-gray-600">{paper.authors.join(', ')}</p>
            </div>
          )}

          {/* Venue */}
          {paper.venue && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-1">Venue</h4>
              <p className="text-sm text-gray-600">{paper.venue}</p>
            </div>
          )}

          {/* Abstract */}
          {paper.abstract && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-1">Abstract</h4>
              <p className="text-sm text-gray-600 leading-relaxed">{paper.abstract}</p>
            </div>
          )}

          {/* Fields of Study */}
          {paper.fields_of_study.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Fields of Study</h4>
              <div className="flex flex-wrap gap-1">
                {paper.fields_of_study.map((field) => (
                  <Badge key={field} variant="secondary" className="text-xs">
                    {field}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Links */}
          <div className="flex flex-wrap gap-3 pt-2">
            {paper.doi && (
              <a
                href={`https://doi.org/${paper.doi}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
              >
                <ExternalLink className="h-4 w-4" />
                DOI: {paper.doi}
              </a>
            )}
            {paper.url && (
              <a
                href={paper.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
              >
                <ExternalLink className="h-4 w-4" />
                View Paper
              </a>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

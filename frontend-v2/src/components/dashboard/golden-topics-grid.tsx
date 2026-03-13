'use client';

import { Zap, ArrowRight } from 'lucide-react';
import { goldenTopics } from '@/types';

interface GoldenTopicsGridProps {
  onTopicSelect: (topic: string) => void;
}

export function GoldenTopicsGrid({ onTopicSelect }: GoldenTopicsGridProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Zap className="h-4 w-4 text-amber-500" />
        <span>Quick start topics</span>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {goldenTopics.map((topic) => (
          <button
            key={topic}
            onClick={() => onTopicSelect(topic)}
            className="group flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3 text-left text-sm transition-all hover:border-blue-200 hover:bg-blue-50"
          >
            <span className="text-gray-700 group-hover:text-gray-900">{topic}</span>
            <ArrowRight className="h-4 w-4 text-gray-400 opacity-0 transition-opacity group-hover:opacity-100" />
          </button>
        ))}
      </div>
    </div>
  );
}

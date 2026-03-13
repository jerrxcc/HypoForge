'use client';

import { Zap, ArrowRight } from 'lucide-react';
import { goldenTopics } from '@/types';
import { Card } from '@/components/primitives';

interface GoldenTopicsGridProps {
  onTopicSelect: (topic: string) => void;
}

export function GoldenTopicsGrid({ onTopicSelect }: GoldenTopicsGridProps) {
  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50">
          <Zap className="h-4 w-4 text-amber-500" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Quick Start Topics</h3>
          <p className="text-sm text-gray-500">Click to start a research run instantly</p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {goldenTopics.map((topic) => (
          <button
            key={topic}
            onClick={() => onTopicSelect(topic)}
            className="group flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-left text-sm transition-all hover:border-blue-300 hover:bg-blue-50 hover:shadow-sm"
          >
            <span className="text-gray-700 group-hover:text-gray-900 line-clamp-2">{topic}</span>
            <ArrowRight className="ml-2 h-4 w-4 flex-shrink-0 text-gray-400 opacity-0 transition-all group-hover:opacity-100 group-hover:text-blue-500" />
          </button>
        ))}
      </div>
    </Card>
  );
}

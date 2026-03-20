'use client';

import { GOLDEN_TOPICS } from '@/lib/constants';

interface GoldenTopicsProps {
  readonly onSelect: (topic: string) => void;
}

export function GoldenTopics({ onSelect }: GoldenTopicsProps) {
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {GOLDEN_TOPICS.map((topic) => (
        <button
          key={topic}
          type="button"
          onClick={() => onSelect(topic)}
          className="cursor-pointer rounded-full bg-secondary px-4 py-2 text-sm text-muted-foreground transition-colors hover:bg-primary/10 hover:text-primary focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
        >
          {topic}
        </button>
      ))}
    </div>
  );
}

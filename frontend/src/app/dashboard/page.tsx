'use client';

import { useState, useCallback } from 'react';
import { ResearchInput } from '@/components/dashboard/research-input';
import { GoldenTopics } from '@/components/dashboard/golden-topics';
import { StatsBar } from '@/components/dashboard/stats-bar';
import { RecentRunsStrip } from '@/components/dashboard/recent-runs-strip';

export default function DashboardPage() {
  const [selectedTopic, setSelectedTopic] = useState<string | undefined>();

  const handleTopicSelect = useCallback((topic: string) => {
    setSelectedTopic(topic);
  }, []);

  return (
    <div className="flex flex-col items-center gap-12 py-16">
      {/* Hero section */}
      <div className="max-w-2xl space-y-3 text-center">
        <h1 className="text-3xl font-semibold sm:text-4xl">
          What do you want to research?
        </h1>
        <p className="text-muted-foreground">
          Enter a scientific topic and HypoForge will generate an auditable
          dossier with papers, evidence, conflict analysis, and ranked hypotheses.
        </p>
      </div>

      {/* Research input */}
      <div className="w-full max-w-xl">
        <ResearchInput externalTopic={selectedTopic} />
      </div>

      {/* Golden topics */}
      <GoldenTopics onSelect={handleTopicSelect} />

      {/* Stats */}
      <div className="w-full max-w-2xl">
        <StatsBar />
      </div>

      {/* Recent runs */}
      <div className="w-full max-w-2xl">
        <RecentRunsStrip />
      </div>
    </div>
  );
}

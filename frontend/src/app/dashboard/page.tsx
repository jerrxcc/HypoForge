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
          Forge your next hypothesis
        </h1>
        <p className="text-muted-foreground">
          Describe a research question and get an auditable dossier — curated papers,
          evidence cards, conflict analysis, and three ranked hypotheses — in minutes.
        </p>
      </div>

      {/* Research input */}
      <div className="w-full max-w-xl">
        <ResearchInput externalTopic={selectedTopic} />
      </div>

      {/* Golden topics */}
      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Or try one of these</h2>
        <GoldenTopics onSelect={handleTopicSelect} />
      </div>

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

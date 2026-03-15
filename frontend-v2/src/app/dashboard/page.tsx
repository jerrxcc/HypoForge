'use client';

import { HeroSection } from '@/components/dashboard/hero-section';
import { QuickStats } from '@/components/dashboard/quick-stats';
import { RecentRuns } from '@/components/dashboard/recent-runs';
import { GoldenTopicsGrid } from '@/components/dashboard/golden-topics-grid';
import { useRouter } from 'next/navigation';
import { useRuns } from '@/hooks/use-runs';
import { Loader2 } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const { data: runs, isLoading } = useRuns();

  const handleTopicSelect = (topic: string) => {
    router.push(`/dashboard/new?topic=${encodeURIComponent(topic)}`);
  };

  // Calculate stats from runs
  const stats = {
    totalRuns: runs?.length ?? 0,
    totalPapers: runs?.reduce((sum, r) => sum + r.selected_paper_count, 0) ?? 0,
    totalEvidence: runs?.reduce((sum, r) => sum + r.evidence_card_count, 0) ?? 0,
    totalHypotheses: runs?.reduce((sum, r) => sum + r.hypothesis_count, 0) ?? 0,
  };

  return (
    <div className="space-y-8">
      <HeroSection />

      {/* Quick Stats - full width */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      ) : (
        <QuickStats {...stats} />
      )}

      {/* Golden Topics - full width like stats */}
      <GoldenTopicsGrid onTopicSelect={handleTopicSelect} />

      <RecentRuns />
    </div>
  );
}

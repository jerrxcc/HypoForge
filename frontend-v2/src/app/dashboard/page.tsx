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
    <div className="space-y-6">
      <HeroSection />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <QuickStats {...stats} />
          )}
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <GoldenTopicsGrid onTopicSelect={handleTopicSelect} />
        </div>
      </div>

      <RecentRuns />
    </div>
  );
}

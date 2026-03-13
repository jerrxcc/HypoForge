'use client';

import { FlaskConical, FileText, GitBranch, Lightbulb } from 'lucide-react';
import { Card } from '@/components/primitives';

interface QuickStatsProps {
  totalRuns: number;
  totalPapers: number;
  totalEvidence: number;
  totalHypotheses: number;
}

export function QuickStats({ totalRuns, totalPapers, totalEvidence, totalHypotheses }: QuickStatsProps) {
  const stats = [
    { label: 'Total Runs', value: totalRuns, icon: FlaskConical, color: 'text-blue-600 bg-blue-50' },
    { label: 'Papers Analyzed', value: totalPapers, icon: FileText, color: 'text-emerald-600 bg-emerald-50' },
    { label: 'Evidence Cards', value: totalEvidence, icon: GitBranch, color: 'text-amber-600 bg-amber-50' },
    { label: 'Hypotheses Generated', value: totalHypotheses, icon: Lightbulb, color: 'text-purple-600 bg-purple-50' },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="p-4">
          <div className="flex items-center gap-3">
            <div className={`rounded-lg p-2 ${stat.color}`}>
              <stat.icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

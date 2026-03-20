'use client';

import { Sparkles } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/primitives';

export function HeroSection() {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 p-8 text-white">
      {/* Background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute -left-4 -top-4 h-40 w-40 rounded-full bg-white blur-3xl" />
        <div className="absolute -bottom-8 -right-8 h-60 w-60 rounded-full bg-white blur-3xl" />
      </div>

      <div className="relative z-10">
        <div className="mb-4 flex items-center gap-2">
          <Sparkles className="h-6 w-6" />
          <span className="text-sm font-medium text-blue-200">AI-Powered Research</span>
        </div>
        <h1 className="mb-4 text-3xl font-bold tracking-tight">
          Generate Scientific Hypotheses
        </h1>
        <p className="mb-6 max-w-xl text-blue-100">
          HypoForge analyzes scientific literature to discover conflicts, extract evidence,
          and generate novel, testable hypotheses for your research.
        </p>
        <Link href="/dashboard/new">
          <Button size="lg" className="bg-white text-blue-700 hover:bg-blue-50">
            Start New Research Run
          </Button>
        </Link>
      </div>
    </div>
  );
}

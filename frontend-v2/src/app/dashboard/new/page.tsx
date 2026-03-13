'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { NewRunForm } from '@/components/run/new-run-form';
import { GoldenTopicsGrid } from '@/components/dashboard/golden-topics-grid';
import { useRouter } from 'next/navigation';

function NewRunPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTopic = searchParams.get('topic') ?? '';

  const handleTopicSelect = (topic: string) => {
    router.push(`/dashboard/new?topic=${encodeURIComponent(topic)}`);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">New Research Run</h1>
        <p className="mt-1 text-gray-500">
          Enter a research topic to generate hypotheses from scientific literature.
        </p>
      </div>

      <NewRunForm initialTopic={initialTopic} />

      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <GoldenTopicsGrid onTopicSelect={handleTopicSelect} />
      </div>
    </div>
  );
}

export default function NewRunPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-2xl">Loading...</div>}>
      <NewRunPageContent />
    </Suspense>
  );
}

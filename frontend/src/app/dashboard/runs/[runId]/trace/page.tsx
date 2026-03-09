import { TraceView } from '@/components/hypoforge/trace-view';

export default async function RunTracePage({
  params
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = await params;
  return <TraceView runId={runId} />;
}

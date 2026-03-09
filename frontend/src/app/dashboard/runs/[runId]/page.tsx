import { RunOverview } from '@/components/hypoforge/run-overview';

export default async function RunOverviewPage({
  params
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = await params;
  return <RunOverview runId={runId} />;
}

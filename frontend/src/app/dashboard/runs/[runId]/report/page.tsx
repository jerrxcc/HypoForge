import { ReportView } from '@/components/hypoforge/report-view';

export default async function RunReportPage({
  params
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = await params;
  return <ReportView runId={runId} />;
}

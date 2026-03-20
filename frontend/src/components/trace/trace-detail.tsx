import { CheckCircle2, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ToolTrace } from '@/types';

interface TraceDetailProps {
  readonly trace: ToolTrace;
}

function JsonBlock({ value }: { readonly value: Record<string, unknown> }) {
  return (
    <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs text-foreground/90">
      <code>{JSON.stringify(value, null, 2)}</code>
    </pre>
  );
}

function Row({ label, children }: { readonly label: string; readonly children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2">
      <span className="w-32 shrink-0 text-xs font-medium text-muted-foreground">{label}</span>
      <span className="min-w-0 flex-1 text-sm text-foreground">{children}</span>
    </div>
  );
}

export function TraceDetail({ trace }: TraceDetailProps) {
  return (
    <Card className="h-full overflow-auto">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">{trace.tool_name}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {/* Meta */}
        <div className="flex flex-col gap-2">
          <Row label="Agent">
            <Badge variant="outline" className="font-mono text-xs">
              {trace.agent_name}
            </Badge>
          </Row>
          <Row label="Model">{trace.model_name}</Row>
          <Row label="Latency">{trace.latency_ms.toLocaleString()}ms</Row>
          {trace.input_tokens != null && (
            <Row label="Tokens in">{trace.input_tokens.toLocaleString()}</Row>
          )}
          {trace.output_tokens != null && (
            <Row label="Tokens out">{trace.output_tokens.toLocaleString()}</Row>
          )}
          <Row label="Status">
            {trace.success ? (
              <span className="flex items-center gap-1 text-success">
                <CheckCircle2 aria-hidden="true" className="size-4" />
                Success
              </span>
            ) : (
              <span className="flex items-center gap-1 text-destructive">
                <XCircle aria-hidden="true" className="size-4" />
                Error
              </span>
            )}
          </Row>
        </div>

        {/* Error */}
        {trace.error_message && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {trace.error_message}
          </div>
        )}

        {/* Args */}
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Arguments
          </span>
          <JsonBlock value={trace.args} />
        </div>

        {/* Result */}
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Result
          </span>
          <JsonBlock value={trace.result_summary} />
        </div>
      </CardContent>
    </Card>
  );
}

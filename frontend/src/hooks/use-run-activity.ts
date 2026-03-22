'use client';

import { useEffect, useRef, useReducer } from 'react';
import { api } from '@/lib/api-client';
import { API_BASE_URL } from '@/lib/constants';
import type { ToolTrace, RunEvent } from '@/types';

export interface RunActivity {
  traces: ToolTrace[];
  activeAgent: string | null;
  activeToolName: string | null;
  stageAttempts: Record<string, number>;
  metrics: { totalTools: number; totalLatencyMs: number };
  connected: boolean;
  error: string | null;
  runTerminal: boolean;
}

const INITIAL_ACTIVITY: RunActivity = {
  traces: [],
  activeAgent: null,
  activeToolName: null,
  stageAttempts: {},
  metrics: { totalTools: 0, totalLatencyMs: 0 },
  connected: false,
  error: null,
  runTerminal: false,
};

type Action =
  | { type: 'reset' }
  | { type: 'connected' }
  | { type: 'merge_traces'; traces: ToolTrace[] }
  | { type: 'sse_event'; event: RunEvent }
  | { type: 'sse_error' };

function reducer(state: RunActivity, action: Action): RunActivity {
  switch (action.type) {
    case 'reset':
      return INITIAL_ACTIVITY;
    case 'connected':
      return { ...state, connected: true, error: null };
    case 'merge_traces': {
      const merged = new Map<string, ToolTrace>();
      for (const t of action.traces) merged.set(t.id, t);
      for (const t of state.traces) merged.set(t.id, t);
      const allTraces = Array.from(merged.values());
      return { ...state, traces: allTraces, metrics: computeMetrics(allTraces) };
    }
    case 'sse_event':
      return applyEvent(state, action.event);
    case 'sse_error':
      return { ...state, connected: false, error: 'SSE connection lost' };
    default:
      return state;
  }
}

export function useRunActivity(runId: string | undefined, enabled: boolean): RunActivity {
  const [activity, dispatch] = useReducer(reducer, INITIAL_ACTIVITY);
  const esRef = useRef<EventSource | null>(null);

  // Reset only when runId changes (not when enabled flips to false)
  useEffect(() => {
    dispatch({ type: 'reset' });
  }, [runId]);

  useEffect(() => {
    if (!runId || !enabled) {
      return;
    }

    let closed = false;

    const es = new EventSource(`${API_BASE_URL}/v1/runs/${runId}/events`);
    esRef.current = es;

    es.addEventListener('open', () => {
      if (closed) return;
      dispatch({ type: 'connected' });

      api.getTrace(runId).then((historicalTraces) => {
        if (closed) return;
        dispatch({ type: 'merge_traces', traces: historicalTraces });
      }).catch(() => {});
    });

    const handleEvent = (e: MessageEvent) => {
      if (closed) return;
      try {
        const event: RunEvent = JSON.parse(e.data);
        dispatch({ type: 'sse_event', event });
      } catch {
        // Ignore malformed events
      }
    };

    es.addEventListener('snapshot', handleEvent);
    es.addEventListener('stage_start', handleEvent);
    es.addEventListener('stage_complete', handleEvent);
    es.addEventListener('tool_start', handleEvent);
    es.addEventListener('tool_complete', handleEvent);
    es.addEventListener('run_complete', handleEvent);
    es.addEventListener('run_error', handleEvent);

    es.addEventListener('error', () => {
      if (closed) return;
      dispatch({ type: 'sse_error' });
    });

    return () => {
      closed = true;
      es.close();
      esRef.current = null;
    };
  }, [runId, enabled]);

  return activity;
}

function applyEvent(prev: RunActivity, event: RunEvent): RunActivity {
  switch (event.type) {
    case 'snapshot':
      return {
        ...prev,
        activeAgent: event.current_activity
          ? String((event.current_activity as Record<string, unknown>).agent_name ?? '')
          : null,
        activeToolName: event.current_activity
          ? String((event.current_activity as Record<string, unknown>).tool_name ?? '')
          : null,
        stageAttempts: event.stage_attempts,
      };

    case 'stage_start':
      return {
        ...prev,
        stageAttempts: {
          ...prev.stageAttempts,
          [event.stage_name]: event.attempt,
        },
      };

    case 'stage_complete':
      return prev;

    case 'tool_start':
      return {
        ...prev,
        activeAgent: event.agent_name,
        activeToolName: event.tool_name,
      };

    case 'tool_complete': {
      const next: RunActivity = {
        ...prev,
        activeAgent: null,
        activeToolName: null,
      };
      if (event.trace_id) {
        const exists = prev.traces.some((t) => t.id === event.trace_id);
        if (!exists) {
          const placeholder: ToolTrace = {
            id: event.trace_id!,
            agent_name: event.agent_name,
            tool_name: event.tool_name,
            stage_name: event.stage_name,
            attempt: event.attempt,
            args: {},
            result_summary: {},
            latency_ms: event.latency_ms ?? 0,
            model_name: '',
            input_tokens: null,
            output_tokens: null,
            request_id: null,
            success: event.success ?? true,
            error_message: event.error ?? null,
            created_at: null,
          };
          next.traces = [...prev.traces, placeholder];
          next.metrics = computeMetrics(next.traces);
        }
      }
      return next;
    }

    case 'run_complete':
    case 'run_error':
      return {
        ...prev,
        activeAgent: null,
        activeToolName: null,
        runTerminal: true,
      };

    default:
      return prev;
  }
}

function computeMetrics(traces: ToolTrace[]): { totalTools: number; totalLatencyMs: number } {
  return {
    totalTools: traces.length,
    totalLatencyMs: traces.reduce((sum, t) => sum + t.latency_ms, 0),
  };
}

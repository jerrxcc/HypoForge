import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge Tailwind classes without conflicts. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a date as a relative human-readable string (e.g. "2 hours ago").
 * Falls back to a locale date string for dates older than 7 days.
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? '' : 's'} ago`;
  if (diffHr < 24) return `${diffHr} hour${diffHr === 1 ? '' : 's'} ago`;
  if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? '' : 's'} ago`;

  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * Format a duration in seconds to a human-readable string (e.g. "1m 23s").
 */
export function formatDuration(seconds: number): string {
  if (seconds < 0) return '—';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return s > 0 ? `${m}m ${s}s` : `${m}m`;
}

/**
 * Truncate a string to maxLength characters, appending an ellipsis if cut.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 1)}…`;
}

type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'degraded';

/**
 * Return a Tailwind text-color class appropriate for a run status.
 */
export function getStatusColor(status: RunStatus): string {
  switch (status) {
    case 'completed':
      return 'text-success';
    case 'running':
      return 'text-primary';
    case 'pending':
      return 'text-muted-foreground';
    case 'failed':
      return 'text-destructive';
    case 'degraded':
      return 'text-warning';
    default:
      return 'text-muted-foreground';
  }
}

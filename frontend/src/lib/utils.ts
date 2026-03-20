import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'done':
      return 'text-emerald-600 bg-emerald-50';
    case 'failed':
      return 'text-rose-600 bg-rose-50';
    case 'queued':
      return 'text-gray-600 bg-gray-50';
    case 'retrieving':
    case 'reviewing':
    case 'criticizing':
    case 'planning':
    case 'reflecting':
      return 'text-blue-600 bg-blue-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
}

export function getStageIndex(stage: string): number {
  const stages = ['retrieval', 'review', 'critic', 'planner'];
  return stages.indexOf(stage);
}

export function getActiveStage(status: string): string | null {
  switch (status) {
    case 'retrieving':
      return 'retrieval';
    case 'reviewing':
      return 'review';
    case 'criticizing':
      return 'critic';
    case 'planning':
      return 'planner';
    case 'reflecting':
      return 'planner'; // reflection happens after planner
    default:
      return null;
  }
}

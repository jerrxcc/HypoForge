import type { Direction } from '@/types';

export function Section({ title, children }: { readonly title: string; readonly children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
      {children}
    </div>
  );
}

export function BulletList({ items }: { readonly items: readonly string[] }) {
  if (items.length === 0) return <p className="text-sm text-muted-foreground">None</p>;
  return (
    <ul className="list-disc pl-4 text-sm space-y-1">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

export function scoreVariant(score: number): 'success' | 'warning' | 'error' {
  if (score >= 0.7) return 'success';
  if (score >= 0.4) return 'warning';
  return 'error';
}

export function directionVariant(direction: Direction): 'success' | 'error' | 'warning' | 'secondary' {
  switch (direction) {
    case 'positive':
      return 'success';
    case 'negative':
      return 'error';
    case 'mixed':
      return 'warning';
    case 'null':
    case 'unclear':
    default:
      return 'secondary';
  }
}

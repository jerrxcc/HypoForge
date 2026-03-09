'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';

const tabs = [
  { slug: '', label: 'Overview' },
  { slug: '/trace', label: 'Trace' },
  { slug: '/report', label: 'Report' }
];

export function RunDetailNav({ runId }: { runId: string }) {
  const pathname = usePathname();

  return (
    <div className='flex flex-wrap gap-2'>
      {tabs.map((tab) => {
        const href = `/dashboard/runs/${runId}${tab.slug}`;
        const active = pathname === href;
        return (
          <Link
            key={tab.label}
            href={href}
            className={cn(
              'rounded-full border px-4 py-2 text-sm transition-colors',
              active
                ? 'border-primary bg-primary text-primary-foreground'
                : 'bg-card text-muted-foreground hover:text-foreground'
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}

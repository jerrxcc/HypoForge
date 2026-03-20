import Link from 'next/link';
import { cn } from '@/lib/utils';

interface LogoProps {
  readonly className?: string;
}

export function Logo({ className }: LogoProps) {
  return (
    <Link href="/dashboard" className={cn('flex items-center gap-2', className)}>
      <div
        className="size-8 rounded-lg"
        aria-hidden="true"
        style={{ background: `linear-gradient(135deg, rgb(var(--logo-from)), rgb(var(--logo-to)))` }}
      />
      <span className="text-lg font-semibold text-foreground">HypoForge</span>
    </Link>
  );
}

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface NavLinkProps {
  readonly href: string;
  readonly children: ReactNode;
}

export function NavLink({ href, children }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={cn(
        'text-sm transition-colors',
        isActive
          ? 'text-primary font-medium'
          : 'text-muted-foreground hover:text-foreground',
      )}
    >
      {children}
    </Link>
  );
}

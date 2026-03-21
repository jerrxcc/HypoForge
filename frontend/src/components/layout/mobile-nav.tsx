'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Home' },
  { href: '/dashboard/runs', label: 'Runs' },
] as const;

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  const handleLinkClick = useCallback(() => {
    setOpen(false);
  }, []);

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={() => setOpen(true)}
        aria-label="Open navigation menu"
      >
        <Menu className="size-5" />
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="top-0 left-0 translate-x-0 translate-y-0 h-full max-w-[min(280px,85vw)] rounded-none border-r">
          <DialogTitle className="sr-only">Navigation</DialogTitle>
          <div className="flex items-center justify-between">
            <span className="text-lg font-semibold">Menu</span>
            <DialogClose asChild>
              <Button variant="ghost" size="icon" aria-label="Close menu">
                <X className="size-5" />
              </Button>
            </DialogClose>
          </div>

          <nav className="mt-4 flex flex-col gap-2">
            {NAV_ITEMS.map(({ href, label }) => {
              const isActive = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  onClick={handleLinkClick}
                  className={cn(
                    'rounded-md px-3 py-2 text-sm transition-colors',
                    isActive
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                  )}
                >
                  {label}
                </Link>
              );
            })}
          </nav>
        </DialogContent>
      </Dialog>
    </>
  );
}

'use client';

import { Logo } from '@/components/layout/logo';
import { NavLink } from '@/components/layout/nav-link';
import { ThemeToggle } from '@/components/layout/theme-toggle';
import { MobileNav } from '@/components/layout/mobile-nav';

export function TopNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur will-change-transform supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 max-w-7xl items-center px-4 sm:px-6 lg:px-8">
        {/* Left: Logo */}
        <Logo />

        {/* Center: Navigation links (hidden on mobile) */}
        <nav className="ml-8 hidden items-center gap-6 md:flex">
          <NavLink href="/dashboard">Home</NavLink>
          <NavLink href="/dashboard/runs">Runs</NavLink>
        </nav>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right: Theme toggle + avatar placeholder */}
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <div
            className="size-8 rounded-full bg-muted"
            aria-hidden="true"
          />
        </div>

        {/* Mobile: Hamburger menu */}
        <div className="ml-2 md:hidden">
          <MobileNav />
        </div>
      </div>
    </header>
  );
}

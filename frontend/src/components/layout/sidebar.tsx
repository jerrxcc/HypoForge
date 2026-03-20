'use client';

import Link from 'next/link';
import { Home, FlaskConical, PlusCircle, Settings, Sparkles } from 'lucide-react';
import { NavItem } from './nav-item';

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-gray-200 bg-white">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-semibold text-gray-900">HypoForge</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-4">
          <NavItem href="/dashboard" label="Dashboard" icon={Home} />
          <NavItem href="/dashboard/new" label="New Run" icon={PlusCircle} />
          <NavItem href="/dashboard/runs" label="All Runs" icon={FlaskConical} />
        </nav>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4">
          <NavItem href="#" label="Settings" icon={Settings} />
        </div>
      </div>
    </aside>
  );
}

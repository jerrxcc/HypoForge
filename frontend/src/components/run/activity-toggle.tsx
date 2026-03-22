'use client';

import { Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ActivityToggleProps {
  readonly open: boolean;
  readonly onToggle: () => void;
  readonly hasActivity: boolean;
}

export function ActivityToggle({ open, onToggle, hasActivity }: ActivityToggleProps) {
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onToggle}
      className={cn(open && 'bg-primary/10 border-primary/30')}
    >
      <Activity className={cn(
        'size-4',
        hasActivity && !open && 'animate-pulse text-primary',
      )} />
      Activity
    </Button>
  );
}

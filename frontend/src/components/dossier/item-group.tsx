'use client';

import { ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { useDossierStore } from '@/stores/dossier-store';
import { cn } from '@/lib/utils';

interface ItemGroupProps {
  readonly groupKey: string;
  readonly label: string;
  readonly count: number;
  readonly children: React.ReactNode;
}

export function ItemGroup({ groupKey, label, count, children }: ItemGroupProps) {
  const expanded = useDossierStore((s) => s.expandedGroups[groupKey] ?? false);
  const toggleGroup = useDossierStore((s) => s.toggleGroup);

  return (
    <Collapsible open={expanded} onOpenChange={() => toggleGroup(groupKey)}>
      <CollapsibleTrigger aria-label={`Toggle ${label} section`} className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium hover:bg-muted/50 transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none">
        <ChevronRight
          className={cn(
            'size-4 shrink-0 text-muted-foreground transition-transform duration-200',
            expanded && 'rotate-90',
          )}
        />
        <span className="flex-1 text-left">{label}</span>
        <Badge variant="secondary" className="text-xs px-1.5 py-0">
          {count}
        </Badge>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="flex flex-col gap-px py-1">
          {children}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

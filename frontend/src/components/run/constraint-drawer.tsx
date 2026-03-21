'use client';

import type { UseFormReturn } from 'react-hook-form';
import { ChevronDown } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import { ConstraintFields } from './constraint-fields';
import type { ConstraintFormValues } from './constraint-fields';

export type { ConstraintFormValues };

interface ConstraintDrawerProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  readonly form: UseFormReturn<ConstraintFormValues, any, any>;
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
}

export function ConstraintDrawer({ form, open, onOpenChange }: ConstraintDrawerProps) {
  return (
    <Collapsible open={open} onOpenChange={onOpenChange}>
      <CollapsibleTrigger className="flex items-center gap-1 rounded text-sm text-muted-foreground hover:text-foreground transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none">
        Show advanced options
        <ChevronDown
          className={cn(
            'size-4 transition-transform',
            open && 'rotate-180',
          )}
        />
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div className="mt-4">
          <ConstraintFields form={form} />
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

'use client';

import { useCallback, useRef } from 'react';
import type { UseFormReturn } from 'react-hook-form';
import { ChevronDown } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import type { RunConstraints } from '@/types';

export type ConstraintFormValues = RunConstraints;

interface ConstraintDrawerProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  readonly form: UseFormReturn<ConstraintFormValues, any, any>;
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
}

function FieldLabel({ children, htmlFor }: { readonly children: React.ReactNode; readonly htmlFor?: string }) {
  return <label htmlFor={htmlFor} className="text-sm font-medium text-foreground">{children}</label>;
}

export function ConstraintDrawer({ form, open, onOpenChange }: ConstraintDrawerProps) {
  const { register, watch, setValue } = form;
  const noveltyWeight = watch('novelty_weight');

  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const handleNoveltyChange = useCallback(
    (value: number[]) => {
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        const novelty = value[0];
        const rounded = Math.round(novelty * 100) / 100;
        const feasibility = Math.round((1 - rounded) * 100) / 100;
        setValue('novelty_weight', rounded, { shouldValidate: true });
        setValue('feasibility_weight', feasibility, { shouldValidate: true });
      }, 100);
    },
    [setValue],
  );

  return (
    <Collapsible open={open} onOpenChange={onOpenChange}>
      <CollapsibleTrigger className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
        Show advanced options
        <ChevronDown
          className={cn(
            'size-4 transition-transform',
            open && 'rotate-180',
          )}
        />
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Year range */}
          <div className="flex flex-col gap-1.5">
            <FieldLabel htmlFor="year-from">Year from</FieldLabel>
            <Input
              id="year-from"
              type="number"
              {...register('year_from', { valueAsNumber: true })}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <FieldLabel htmlFor="year-to">Year to</FieldLabel>
            <Input
              id="year-to"
              type="number"
              {...register('year_to', { valueAsNumber: true })}
            />
          </div>

          {/* Max papers */}
          <div className="flex flex-col gap-1.5">
            <FieldLabel htmlFor="max-papers">Max papers</FieldLabel>
            <Input
              id="max-papers"
              type="number"
              {...register('max_selected_papers', { valueAsNumber: true })}
            />
          </div>

          {/* Lab mode */}
          <div className="flex flex-col gap-1.5">
            <FieldLabel>Lab mode</FieldLabel>
            <Select
              value={watch('lab_mode')}
              onValueChange={(value: 'wet' | 'dry' | 'either') =>
                setValue('lab_mode', value, { shouldValidate: true })
              }
            >
              <SelectTrigger aria-label="Lab mode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="wet">Wet</SelectItem>
                <SelectItem value="dry">Dry</SelectItem>
                <SelectItem value="either">Either</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Open access */}
          <div className="flex items-center gap-3 sm:col-span-2">
            <Switch
              id="open-access"
              checked={watch('open_access_only')}
              onCheckedChange={(checked: boolean) =>
                setValue('open_access_only', checked, { shouldValidate: true })
              }
            />
            <FieldLabel htmlFor="open-access">Open access only</FieldLabel>
          </div>

          {/* Novelty weight slider */}
          <div className="flex flex-col gap-2 sm:col-span-2">
            <div className="flex items-center justify-between">
              <FieldLabel>Novelty weight</FieldLabel>
              <span className="text-sm text-muted-foreground">{noveltyWeight.toFixed(2)}</span>
            </div>
            <Slider
              aria-label="Novelty weight"
              value={[noveltyWeight]}
              onValueChange={handleNoveltyChange}
              min={0}
              max={1}
              step={0.05}
            />
          </div>

          {/* Feasibility weight (read-only display) */}
          <div className="flex flex-col gap-2 sm:col-span-2">
            <div className="flex items-center justify-between">
              <FieldLabel>Feasibility weight</FieldLabel>
              <span className="text-sm text-muted-foreground">
                {watch('feasibility_weight').toFixed(2)}
              </span>
            </div>
            <Slider
              aria-label="Feasibility weight (auto-calculated)"
              value={[watch('feasibility_weight')]}
              min={0}
              max={1}
              step={0.05}
              disabled
            />
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

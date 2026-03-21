'use client';

import { useCallback, useEffect, useRef } from 'react';
import type { UseFormReturn } from 'react-hook-form';
import { useWatch } from 'react-hook-form';
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
import type { RunConstraints } from '@/types';

export type ConstraintFormValues = RunConstraints;

export function FieldLabel({ children, htmlFor }: { readonly children: React.ReactNode; readonly htmlFor?: string }) {
  return <label htmlFor={htmlFor} className="text-sm font-medium text-foreground">{children}</label>;
}

interface ConstraintFieldsProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  readonly form: UseFormReturn<ConstraintFormValues, any, any>;
  /** Prefix for input ids to avoid collisions when rendered multiple times on the same page. */
  readonly idPrefix?: string;
}

export function ConstraintFields({ form, idPrefix = '' }: ConstraintFieldsProps) {
  const { register, setValue, control } = form;
  const [noveltyWeight, labMode, openAccessOnly, feasibilityWeight] = useWatch({
    control,
    name: ['novelty_weight', 'lab_mode', 'open_access_only', 'feasibility_weight'],
  });

  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timerRef.current), []);
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

  const id = (name: string) => (idPrefix ? `${idPrefix}-${name}` : name);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div className="flex flex-col gap-1.5">
        <FieldLabel htmlFor={id('year-from')}>Year from</FieldLabel>
        <Input id={id('year-from')} type="number" {...register('year_from', { valueAsNumber: true })} />
      </div>
      <div className="flex flex-col gap-1.5">
        <FieldLabel htmlFor={id('year-to')}>Year to</FieldLabel>
        <Input id={id('year-to')} type="number" {...register('year_to', { valueAsNumber: true })} />
      </div>

      <div className="flex flex-col gap-1.5">
        <FieldLabel htmlFor={id('max-papers')}>Max papers</FieldLabel>
        <Input id={id('max-papers')} type="number" {...register('max_selected_papers', { valueAsNumber: true })} />
      </div>

      <div className="flex flex-col gap-1.5">
        <FieldLabel htmlFor={id('lab-mode')}>Lab mode</FieldLabel>
        <Select
          value={labMode}
          onValueChange={(value: 'wet' | 'dry' | 'either') =>
            setValue('lab_mode', value, { shouldValidate: true })
          }
        >
          <SelectTrigger id={id('lab-mode')}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="wet">Wet</SelectItem>
            <SelectItem value="dry">Dry</SelectItem>
            <SelectItem value="either">Either</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center gap-3 sm:col-span-2">
        <Switch
          id={id('open-access')}
          checked={openAccessOnly}
          onCheckedChange={(checked: boolean) =>
            setValue('open_access_only', checked, { shouldValidate: true })
          }
        />
        <FieldLabel htmlFor={id('open-access')}>Open access only</FieldLabel>
      </div>

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

      <div className="flex flex-col gap-2 sm:col-span-2">
        <div className="flex items-center justify-between">
          <FieldLabel>Feasibility weight</FieldLabel>
          <span className="text-sm text-muted-foreground">
            {feasibilityWeight.toFixed(2)}
          </span>
        </div>
        <Slider
          aria-label="Feasibility weight (auto-calculated)"
          value={[feasibilityWeight]}
          min={0}
          max={1}
          step={0.05}
          disabled
        />
      </div>
    </div>
  );
}

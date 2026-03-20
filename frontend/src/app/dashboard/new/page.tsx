'use client';

import { use, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import { topicSchema, type TopicFormValues } from '@/lib/schemas';
import { useLaunchRun } from '@/hooks/use-launch-run';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { UseFormReturn } from 'react-hook-form';
import type { ConstraintFormValues } from '@/components/run/constraint-drawer';

function FieldLabel({ children }: { readonly children: React.ReactNode }) {
  return <label className="text-sm font-medium text-foreground">{children}</label>;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ConstraintFields({ form }: { readonly form: UseFormReturn<ConstraintFormValues, any, any> }) {
  const { register, watch, setValue } = form;
  const noveltyWeight = watch('novelty_weight');

  const handleNoveltyChange = (value: number[]) => {
    const novelty = value[0];
    const rounded = Math.round(novelty * 100) / 100;
    const feasibility = Math.round((1 - rounded) * 100) / 100;
    setValue('novelty_weight', rounded, { shouldValidate: true });
    setValue('feasibility_weight', feasibility, { shouldValidate: true });
  };

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div className="flex flex-col gap-1.5">
        <FieldLabel>Year from</FieldLabel>
        <Input type="number" {...register('year_from', { valueAsNumber: true })} />
      </div>
      <div className="flex flex-col gap-1.5">
        <FieldLabel>Year to</FieldLabel>
        <Input type="number" {...register('year_to', { valueAsNumber: true })} />
      </div>
      <div className="flex flex-col gap-1.5">
        <FieldLabel>Max papers</FieldLabel>
        <Input type="number" {...register('max_selected_papers', { valueAsNumber: true })} />
      </div>
      <div className="flex flex-col gap-1.5">
        <FieldLabel>Lab mode</FieldLabel>
        <Select
          value={watch('lab_mode')}
          onValueChange={(value: 'wet' | 'dry' | 'either') =>
            setValue('lab_mode', value, { shouldValidate: true })
          }
        >
          <SelectTrigger>
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
          checked={watch('open_access_only')}
          onCheckedChange={(checked: boolean) =>
            setValue('open_access_only', checked, { shouldValidate: true })
          }
        />
        <FieldLabel>Open access only</FieldLabel>
      </div>
      <div className="flex flex-col gap-2 sm:col-span-2">
        <div className="flex items-center justify-between">
          <FieldLabel>Novelty weight</FieldLabel>
          <span className="text-sm text-muted-foreground">{noveltyWeight.toFixed(2)}</span>
        </div>
        <Slider
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
            {watch('feasibility_weight').toFixed(2)}
          </span>
        </div>
        <Slider
          value={[watch('feasibility_weight')]}
          min={0}
          max={1}
          step={0.05}
          disabled
        />
      </div>
    </div>
  );
}

const DEFAULT_CONSTRAINTS: ConstraintFormValues = {
  year_from: 2018,
  year_to: 2026,
  max_selected_papers: 36,
  open_access_only: false,
  lab_mode: 'either',
  novelty_weight: 0.5,
  feasibility_weight: 0.5,
};

export default function NewRunPage({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string }>;
}) {
  const { topic: topicParam } = use(searchParams);
  const router = useRouter();
  const launchRun = useLaunchRun();

  const topicForm = useForm<TopicFormValues>({
    resolver: zodResolver(topicSchema),
    defaultValues: { topic: topicParam ?? '' },
  });

  const constraintForm = useForm<ConstraintFormValues>({
    defaultValues: DEFAULT_CONSTRAINTS,
  });

  const isSubmitting = launchRun.isPending;

  const onSubmit = useCallback(
    async (values: TopicFormValues) => {
      try {
        const constraints = constraintForm.getValues();
        const result = await launchRun.mutateAsync({
          topic: values.topic,
          constraints,
        });
        router.push(`/dashboard/runs/${result.run_id}`);
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to launch run';
        toast.error(message);
      }
    },
    [launchRun, constraintForm, router],
  );

  return (
    <div className="mx-auto max-w-2xl py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-foreground">New Research Run</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter a research topic and configure the run parameters below.
        </p>
      </div>

      <form onSubmit={topicForm.handleSubmit(onSubmit)} className="space-y-6">
        {/* Topic input */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="topic" className="text-sm font-medium text-foreground">
            Research Topic
          </label>
          <Input
            id="topic"
            {...topicForm.register('topic')}
            placeholder="e.g. solid-state battery electrolyte interfaces"
            disabled={isSubmitting}
            className="h-12 text-base"
          />
          {topicForm.formState.errors.topic && (
            <p className="text-sm text-destructive">
              {topicForm.formState.errors.topic.message}
            </p>
          )}
        </div>

        {/* Constraints — always visible */}
        <div className="rounded-lg border border-border p-4 space-y-4">
          <p className="text-sm font-medium text-foreground">Advanced Options</p>
          <ConstraintFields form={constraintForm} />
        </div>

        {/* Submit */}
        <Button
          type="submit"
          disabled={isSubmitting}
          size="lg"
          className="w-full gap-2"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Launching…
            </>
          ) : (
            <>
              Launch Research
              <ArrowRight className="size-4" />
            </>
          )}
        </Button>
      </form>
    </div>
  );
}

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
import { ConstraintFields, type ConstraintFormValues } from '@/components/run/constraint-fields';

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

        {/* Constraints */}
        <div className="rounded-lg border border-border p-4 space-y-4">
          <p className="text-sm font-medium text-foreground">Advanced Options</p>
          <ConstraintFields form={constraintForm} idPrefix="new" />
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

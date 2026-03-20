'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowRight, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { topicSchema, type TopicFormValues } from '@/lib/schemas';
import { useLaunchRun } from '@/hooks/use-launch-run';
import { Input } from '@/components/ui/input';
import { ConstraintDrawer, type ConstraintFormValues } from '@/components/run/constraint-drawer';

interface ResearchInputProps {
  /** Externally-set topic value (e.g. from golden topics click). */
  readonly externalTopic?: string;
}

export function ResearchInput({ externalTopic }: ResearchInputProps) {
  const router = useRouter();
  const launchRun = useLaunchRun();
  const [constraintsOpen, setConstraintsOpen] = useState(false);

  const topicForm = useForm<TopicFormValues>({
    resolver: zodResolver(topicSchema),
    defaultValues: { topic: '' },
  });

  const constraintForm = useForm<ConstraintFormValues>({
    defaultValues: {
      year_from: 2018,
      year_to: 2026,
      max_selected_papers: 36,
      open_access_only: false,
      lab_mode: 'either' as const,
      novelty_weight: 0.5,
      feasibility_weight: 0.5,
    } satisfies ConstraintFormValues,
  });

  // Sync external topic into form
  useEffect(() => {
    if (externalTopic) {
      topicForm.setValue('topic', externalTopic, { shouldValidate: true });
    }
  }, [externalTopic, topicForm]);

  const isSubmitting = launchRun.isPending;

  const onSubmit = useCallback(
    async (values: TopicFormValues) => {
      try {
        const constraints = constraintsOpen
          ? constraintForm.getValues()
          : undefined;
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
    [launchRun, constraintForm, constraintsOpen, router],
  );

  return (
    <div className="w-full space-y-4">
      <form onSubmit={topicForm.handleSubmit(onSubmit)} className="relative">
        <label htmlFor="topic-input" className="sr-only">Research topic</label>
        <Input
          {...topicForm.register('topic')}
          id="topic-input"
          placeholder="e.g., CRISPR delivery mechanisms in solid tumors"
          disabled={isSubmitting}
          className="h-14 rounded-full pl-6 pr-14 text-base shadow-md"
        />
        <button
          type="submit"
          disabled={isSubmitting}
          className="absolute right-2 top-1/2 -translate-y-1/2 flex size-10 items-center justify-center rounded-full bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
          aria-label="Start research"
        >
          {isSubmitting ? (
            <Loader2 className="size-5 animate-spin" />
          ) : (
            <ArrowRight className="size-5" />
          )}
        </button>
        {topicForm.formState.errors.topic && (
          <p className="mt-2 text-sm text-destructive">
            {topicForm.formState.errors.topic.message}
          </p>
        )}
      </form>

      <div className="flex justify-center">
        <ConstraintDrawer
          form={constraintForm}
          open={constraintsOpen}
          onOpenChange={setConstraintsOpen}
        />
      </div>
    </div>
  );
}

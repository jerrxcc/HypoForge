'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRouter } from 'next/navigation';
import { Loader2, Sparkles } from 'lucide-react';
import { Button, Input, Card } from '@/components/primitives';
import { launchRun } from '@/lib/api-client';
import { defaultConstraints } from '@/types';

const formSchema = z.object({
  topic: z.string().min(3, 'Topic must be at least 3 characters'),
});

type FormData = z.infer<typeof formSchema>;

interface NewRunFormProps {
  initialTopic?: string;
}

export function NewRunForm({ initialTopic = '' }: NewRunFormProps) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: { topic: initialTopic },
  });

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const result = await launchRun({
        topic: data.topic,
        constraints: defaultConstraints as unknown as Record<string, unknown>,
      });

      // Navigate to the run detail page
      router.push(`/dashboard/runs/${result.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start run');
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <label htmlFor="topic" className="mb-2 block text-sm font-medium text-gray-700">
            Research Topic
          </label>
          <Input
            id="topic"
            placeholder="e.g., solid-state battery electrolyte"
            className="h-12 text-base"
            {...register('topic')}
          />
          {errors.topic && (
            <p className="mt-1 text-sm text-rose-600">{errors.topic.message}</p>
          )}
          {error && (
            <p className="mt-1 text-sm text-rose-600">{error}</p>
          )}
        </div>

        <div className="flex items-center gap-4">
          <Button type="submit" size="lg" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Start Research Run
              </>
            )}
          </Button>
          <span className="text-sm text-gray-500">
            This will take a few minutes to complete
          </span>
        </div>
      </form>
    </Card>
  );
}

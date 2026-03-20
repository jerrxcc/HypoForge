'use client';

import { useState } from 'react';
import { Loader2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useRerunPlanner } from '@/hooks/use-rerun-planner';
import type { RunStatus } from '@/types';

interface RerunPlannerButtonProps {
  readonly runId: string;
  readonly status: RunStatus;
}

export function RerunPlannerButton({ runId, status }: RerunPlannerButtonProps) {
  const [open, setOpen] = useState(false);
  const mutation = useRerunPlanner(runId);

  const handleConfirm = () => {
    mutation.mutate(undefined, {
      onSuccess: () => {
        setOpen(false);
        toast.success('Planner rerun started');
      },
      onError: (error) => {
        setOpen(false);
        const message = error.message.includes('409')
          ? 'Cannot rerun -- run is still in progress'
          : error.message;
        toast.error('Rerun failed', { description: message });
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={status !== 'done'}
        >
          {mutation.isPending ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <RefreshCw className="size-4" />
          )}
          Rerun Planner
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Rerun Planner?</DialogTitle>
          <DialogDescription>
            This will regenerate hypotheses using existing evidence and conflicts.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={mutation.isPending}>
            {mutation.isPending && <Loader2 className="size-4 animate-spin" />}
            Confirm
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

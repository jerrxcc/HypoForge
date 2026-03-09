import { Button } from '@/components/ui/button';
import { goldenTopics } from '@/lib/hypoforge';

export function GoldenTopicLauncher({
  onPick
}: {
  onPick: (topic: string) => void;
}) {
  return (
    <div className='flex flex-wrap gap-2'>
      {goldenTopics.map((topic) => (
        <Button
          key={topic}
          type='button'
          variant='outline'
          className='h-auto max-w-full rounded-full px-4 py-2 text-left leading-snug whitespace-normal'
          onClick={() => onPick(topic)}
        >
          {topic}
        </Button>
      ))}
    </div>
  );
}

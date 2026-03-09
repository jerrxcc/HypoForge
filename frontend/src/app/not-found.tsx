'use client';

import { useRouter } from 'next/navigation';

import { Button } from '@/components/ui/button';

export default function NotFound() {
  const router = useRouter();

  return (
    <div className='absolute top-1/2 left-1/2 mb-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center text-center'>
      <span className='from-foreground bg-linear-to-b to-transparent bg-clip-text text-[10rem] leading-none font-extrabold text-transparent'>
        404
      </span>
      <h2 className='my-2 font-serif text-3xl font-semibold'>
        Something&apos;s missing
      </h2>
      <p className='text-muted-foreground'>
        The route exists in neither the old starter nor the new HypoForge
        shell.
      </p>
      <div className='mt-8 flex justify-center gap-2'>
        <Button onClick={() => router.back()} variant='default' size='lg'>
          Go back
        </Button>
        <Button
          onClick={() => router.push('/dashboard/new-run')}
          variant='ghost'
          size='lg'
        >
          Back to Console
        </Button>
      </div>
    </div>
  );
}

import { NewRunForm } from '@/components/hypoforge/new-run-form';

export default function NewRunPage() {
  return (
    <div className='mx-auto flex w-full max-w-[1680px] flex-1 flex-col gap-6 p-4 md:p-8'>
      <NewRunForm />
    </div>
  );
}

import Link from 'next/link';

export default function RunNotFound() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24">
      <h1 className="text-xl font-semibold">Run not found</h1>
      <p className="text-muted-foreground">
        This run may have been deleted or doesn&apos;t exist.
      </p>
      <Link href="/dashboard/runs" className="text-primary hover:underline">
        Back to Runs
      </Link>
    </div>
  );
}

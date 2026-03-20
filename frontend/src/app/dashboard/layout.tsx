import { TopNav } from '@/components/layout/top-nav';

export default function DashboardLayout({ children }: { readonly children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="animate-[fade-in_0.25s_ease-out]">
          {children}
        </div>
      </main>
    </div>
  );
}

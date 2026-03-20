import { TopNav } from '@/components/layout/top-nav';

export default function DashboardLayout({ children }: { readonly children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-4 focus:py-2 focus:text-sm focus:shadow-md">Skip to content</a>
      <TopNav />
      <main id="main-content" className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="animate-[fade-in_0.25s_ease-out]">
          {children}
        </div>
      </main>
    </div>
  );
}

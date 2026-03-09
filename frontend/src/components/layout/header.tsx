import React from 'react';
import { SidebarTrigger } from '../ui/sidebar';
import { Separator } from '../ui/separator';
import { Breadcrumbs } from '../breadcrumbs';
import SearchInput from '../search-input';
import { ThemeModeToggle } from '../themes/theme-mode-toggle';
import { Badge } from '../ui/badge';

export default function Header() {
  return (
    <header className='bg-background/92 supports-[backdrop-filter]:bg-background/75 sticky top-0 z-40 flex h-16 shrink-0 items-center justify-between gap-2 border-b backdrop-blur transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12'>
      <div className='flex items-center gap-2 px-4'>
        <SidebarTrigger className='-ml-1' />
        <Separator orientation='vertical' className='mr-2 h-4' />
        <Breadcrumbs />
      </div>

      <div className='flex items-center gap-2 px-4'>
        <Badge variant='outline' className='hidden md:inline-flex'>
          Academic editorial desk
        </Badge>
        <div className='hidden md:flex'>
          <SearchInput />
        </div>
        <ThemeModeToggle />
      </div>
    </header>
  );
}

'use client';

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail
} from '@/components/ui/sidebar';
import { navItems } from '@/config/nav-config';
import { useFilteredNavItems } from '@/hooks/use-nav';
import {
  IconFlask2,
  IconProgressCheck,
  IconRosetteDiscountCheck
} from '@tabler/icons-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Icons } from '../icons';
import { Badge } from '../ui/badge';

export default function AppSidebar() {
  const pathname = usePathname();
  const filteredItems = useFilteredNavItems(navItems);

  return (
    <Sidebar collapsible='icon'>
      <SidebarHeader>
        <div className='flex items-center gap-3 px-2 py-3'>
          <div className='bg-primary/12 text-primary flex size-10 items-center justify-center rounded-2xl border border-current/15'>
            <IconFlask2 className='size-5' />
          </div>
          <div className='min-w-0 group-data-[collapsible=icon]/sidebar:hidden'>
            <p className='font-serif text-base font-semibold tracking-tight'>
              HypoForge
            </p>
            <p className='text-muted-foreground text-xs'>
              Research orchestration desk
            </p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent className='overflow-x-hidden'>
        <SidebarGroup>
          <SidebarGroupLabel>Console</SidebarGroupLabel>
          <SidebarMenu>
            {filteredItems.map((item) => {
              const Icon = item.icon ? Icons[item.icon] : Icons.logo;

              return (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    tooltip={item.title}
                    isActive={pathname === item.url || pathname.startsWith(`${item.url}/`)}
                  >
                    <Link href={item.url}>
                      <Icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <div className='bg-sidebar-accent/55 rounded-2xl border border-sidebar-border px-3 py-3 group-data-[collapsible=icon]/sidebar:px-2'>
          <div className='flex items-center gap-2'>
            <IconProgressCheck className='text-primary size-4 shrink-0' />
            <p className='text-sm font-medium group-data-[collapsible=icon]/sidebar:hidden'>
              Live research pipeline
            </p>
          </div>
          <p className='text-muted-foreground mt-2 text-xs leading-5 group-data-[collapsible=icon]/sidebar:hidden'>
            Shell scaffolded for real runs, trace review, and markdown report reading.
          </p>
          <Badge
            variant='secondary'
            className='mt-3 gap-1 group-data-[collapsible=icon]/sidebar:hidden'
          >
            <IconRosetteDiscountCheck className='size-3.5' />
            Demo mode
          </Badge>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}

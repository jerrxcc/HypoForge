import { NavItem } from '@/types';

export const navItems: NavItem[] = [
  {
    title: 'New Run',
    url: '/dashboard/new-run',
    icon: 'dashboard',
    isActive: true,
    shortcut: ['n', 'r'],
    items: []
  },
  {
    title: 'Runs',
    url: '/dashboard/runs',
    icon: 'workspace',
    isActive: false,
    shortcut: ['r', 'u'],
    items: []
  }
];

import { IBM_Plex_Mono, IBM_Plex_Sans, Newsreader } from 'next/font/google';

import { cn } from '@/lib/utils';

const fontSans = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-sans'
});

const fontMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-mono'
});

const fontSerif = Newsreader({
  subsets: ['latin'],
  variable: '--font-serif'
});

export const fontVariables = cn(
  fontSans.variable,
  fontMono.variable,
  fontSerif.variable
);

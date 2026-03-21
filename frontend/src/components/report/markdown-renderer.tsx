import ReactMarkdown from 'react-markdown';
import { ScrollArea } from '@/components/ui/scroll-area';

interface MarkdownRendererProps {
  readonly content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ScrollArea className="h-full">
      <article aria-label="Research report" className="prose prose-sm sm:prose prose-neutral dark:prose-invert max-w-none prose-headings:text-foreground prose-p:text-foreground/90 prose-a:text-primary p-4 sm:p-6">
        <ReactMarkdown>{content}</ReactMarkdown>
      </article>
    </ScrollArea>
  );
}

import React, { useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';

type MarkdownCodeProps = React.ComponentProps<'code'> & {
  inline?: boolean;
};

interface MessageBubbleProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export const MessageBubble: React.FC<MessageBubbleProps> = React.memo(({ role, content }) => {
  const isUser = role === 'user';
  const bubbleRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    gsap.fromTo(
      bubbleRef.current,
      { opacity: 0, y: 15, scale: 0.95 },
      { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(1.5)" }
    );
  }, { scope: bubbleRef });

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div 
        ref={bubbleRef}
        className={`relative max-w-[85%] lg:max-w-3xl w-fit break-words ${
          isUser 
            ? 'bg-primary-500/90 dark:bg-primary-500/80 backdrop-blur-md rounded-2xl rounded-tr-sm px-5 py-3 text-white shadow-sm dark:shadow-ai-glow'
            : 'bg-white/80 dark:bg-white/5 backdrop-blur-xl border border-slate-200/60 dark:border-white/10 rounded-2xl rounded-tl-sm px-5 py-3 text-slate-800 dark:text-slate-100 shadow-sm dark:shadow-glass-widget'
        }`}
      >
        <ReactMarkdown
          components={{
            code(props: MarkdownCodeProps) {
              const { inline, className, children, ...rest } = props;
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <div className="w-full max-w-full overflow-x-auto rounded-md my-3 border border-white/10 bg-[#1E1E1E]">
                  <div className="flex items-center px-4 py-1.5 bg-black/40 border-b border-white/5 text-xs text-slate-400 font-mono uppercase tracking-wider">
                    {match[1]}
                  </div>
                  <SyntaxHighlighter 
                    style={vscDarkPlus as Record<string, React.CSSProperties>} 
                    language={match[1]} 
                    PreTag="div" 
                    customStyle={{ background: 'transparent', margin: 0, padding: '1rem', fontSize: '14px' }} 
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                </div>
              ) : (
                <code className="bg-black/30 text-primary-300 rounded px-1.5 py-0.5 font-mono text-sm" {...rest}>
                  {children}
                </code>
              );
            },
            p: ({children}) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
            ul: ({children}) => <ul className="list-disc ml-6 mb-2">{children}</ul>,
            ol: ({children}) => <ol className="list-decimal ml-6 mb-2">{children}</ol>,
            a: ({children, href}) => {
              if (href === 'auto-email-event') {
                return <span className="text-purple-400 font-semibold">{children}</span>;
              }
              return <a href={href} className="text-primary-400 hover:underline">{children}</a>;
            }
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
});
MessageBubble.displayName = 'MessageBubble';

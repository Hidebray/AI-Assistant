import React, { useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { Copy, Check } from 'lucide-react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CodeBlock = ({ match, children }: any) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    const code = String(children).replace(/\n$/, '');
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full max-w-full overflow-x-auto rounded-md my-3 border border-white/10 bg-[#1E1E1E] group">
      <div className="flex items-center justify-between px-4 py-1.5 bg-black/40 border-b border-white/5">
        <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">
          {match[1]}
        </div>
        <button 
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors text-xs font-medium opacity-0 group-hover:opacity-100"
        >
          {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
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
  );
};

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
            ? 'bg-gradient-to-br from-primary-500 to-primary-600 backdrop-blur-md rounded-2xl rounded-tr-sm px-5 py-3.5 text-white shadow-md dark:shadow-ai-glow border border-primary-400/30'
            : 'bg-white/90 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200/80 dark:border-white/10 rounded-2xl rounded-tl-sm px-5 py-3.5 text-slate-800 dark:text-slate-100 shadow-sm dark:shadow-glass-widget'
        }`}
      >
        {(!content && !isUser) ? (
          <div className="flex items-center gap-1.5 h-6 px-1">
            <div className="w-2 h-2 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        ) : (
          <ReactMarkdown
            components={{
              code(props: MarkdownCodeProps) {
                const { inline, className, children, ...rest } = props;
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <CodeBlock match={match} children={children} />
                ) : (
                  <code className="bg-slate-100 dark:bg-black/30 text-primary-600 dark:text-primary-300 rounded px-1.5 py-0.5 font-mono text-sm" {...rest}>
                    {children}
                  </code>
                );
              },
              p: ({children}) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
              ul: ({children}) => <ul className="list-disc ml-6 mb-2">{children}</ul>,
              ol: ({children}) => <ol className="list-decimal ml-6 mb-2">{children}</ol>,
              a: ({children, href}) => {
                if (href === 'auto-email-event') {
                  return <span className="text-purple-600 dark:text-purple-400 font-semibold">{children}</span>;
                }
                return <a href={href} className="text-primary-600 dark:text-primary-400 hover:underline">{children}</a>;
              }
            }}
          >
            {content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
});
MessageBubble.displayName = 'MessageBubble';

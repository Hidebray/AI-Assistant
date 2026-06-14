import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import gsap from 'gsap';
import { useChatStore } from '../../core/store/useChatStore';
import { Sparkles } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

export const AgentStatusIndicator: React.FC = () => {
  const isStreaming = useChatStore((state) => state.isStreaming);
  const coreRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (isStreaming && coreRef.current && glowRef.current) {
      const tl = gsap.timeline({ repeat: -1, yoyo: true });
      tl.to(coreRef.current, { scale: 1.1, opacity: 1, duration: 1.2, ease: "sine.inOut" });
      gsap.to(glowRef.current, { rotation: 360, duration: 3, repeat: -1, ease: "linear", transformOrigin: "center center" });
    }
  }, [isStreaming]);

  return (
    <div className="flex items-center gap-3">
      <div className="relative w-8 h-8 flex items-center justify-center rounded-full bg-black/40 border border-white/10 overflow-hidden">
        {/* Glow Spinner */}
        <div 
          ref={glowRef}
          className={twMerge(
            "absolute inset-[-150%] bg-gradient-to-tr from-transparent via-primary-glow to-transparent opacity-0 transition-opacity duration-500",
            isStreaming && "opacity-60"
          )}
        />
        {/* Core background */}
        <div className="absolute inset-[2px] rounded-full bg-slate-900 flex items-center justify-center z-10">
          <div ref={coreRef} className={twMerge("text-primary-500", isStreaming ? "opacity-100" : "opacity-50")}>
            <Sparkles size={14} />
          </div>
        </div>
      </div>
      <div className="flex flex-col">
        <span className="text-sm font-medium text-white leading-tight">AI-Assistant</span>
        <span className="text-xs text-slate-400">
          {isStreaming ? (
            <span className="text-primary-400 animate-pulse">Thinking...</span>
          ) : "Ready"}
        </span>
      </div>
    </div>
  );
};

import React, { useRef, useEffect, useState } from 'react';
import { Square, ArrowUp, Mic, Zap } from 'lucide-react';
import { useChatStore } from '../../core/store/useChatStore';
import { useSpeechRecognition } from './useSpeechRecognition';
import { PromptLibrary } from './PromptLibrary';
import { useTranslation } from 'react-i18next';

interface ChatInputProps {
  sendMessage: (content: string) => void;
  stopGenerating: () => void;
  isNewChat?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ sendMessage, stopGenerating, isNewChat = false }) => {
  const [input, setInput] = useState('');
  const [baseInput, setBaseInput] = useState('');
  const [isPromptLibraryOpen, setIsPromptLibraryOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { t } = useTranslation();
  const isStreaming = useChatStore((state) => state.isStreaming);

  const { isListening, toggleListening, isSupported } = useSpeechRecognition((transcript) => {
    setInput(baseInput + (baseInput && transcript ? ' ' : '') + transcript);
  });

  const pendingDraftMessage = useChatStore(state => state.pendingDraftMessage);
  const setPendingDraftMessage = useChatStore(state => state.setPendingDraftMessage);

  useEffect(() => {
    if (pendingDraftMessage) {
      setInput(pendingDraftMessage);
      setPendingDraftMessage(null);
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [pendingDraftMessage, setPendingDraftMessage]);

  const handleToggleMic = () => {
    if (!isListening) {
      setBaseInput(input);
    }
    toggleListening();
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isStreaming) return;
    if (isListening) toggleListening();
    sendMessage(input.trim());
    setInput('');
    setBaseInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handlePromptSelect = (prompt: string) => {
    setInput(prompt);
    setIsPromptLibraryOpen(false);
    // Optional: focus the textarea
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="w-full px-6 py-4">
      <div className="max-w-4xl mx-auto w-full relative group">
        <div className="bg-white/95 dark:bg-slate-900/70 backdrop-blur-3xl border border-slate-200/80 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20 hover:shadow-xl dark:hover:shadow-glass-widget-hover shadow-lg dark:shadow-glass-widget rounded-3xl flex flex-col p-2.5 transition-all duration-300 focus-within:border-primary-500/50 focus-within:shadow-[0_8px_30px_rgba(99,102,241,0.15)] dark:focus-within:shadow-ai-glow focus-within:bg-white dark:focus-within:bg-slate-900/90 group-hover:-translate-y-0.5">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('chat.placeholder')}
            className="w-full max-h-40 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 outline-none resize-none px-3 py-2 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-white/10"
            rows={1}
          />
          <div className="flex justify-between items-center mt-2 px-1 relative">
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setIsPromptLibraryOpen(!isPromptLibraryOpen)}
                className={`p-2 rounded-lg transition-colors ${
                  isPromptLibraryOpen 
                    ? 'bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400' 
                    : 'text-slate-400 hover:text-amber-500 dark:hover:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-500/10'
                }`}
                title={t('promptLibrary.title')}
              >
                <Zap size={20} />
              </button>
              {isPromptLibraryOpen && (
                <PromptLibrary 
                  onSelect={handlePromptSelect} 
                  onClose={() => setIsPromptLibraryOpen(false)} 
                />
              )}
            </div>
            
            {isStreaming ? (
              <button 
                onClick={stopGenerating}
                className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-white/10 hover:bg-slate-200 dark:hover:bg-white/20 text-slate-700 dark:text-white rounded-xl transition-colors font-medium"
              >
                <Square size={16} className="fill-white" />
                {t('chat.stop')}
              </button>
            ) : (
              <div className="flex items-center gap-2">
                {(isListening || !input.trim()) && (
                  <button 
                    onClick={handleToggleMic}
                    className={`p-2 rounded-xl transition-all active:scale-95 ${
                      isListening 
                        ? 'bg-red-500 hover:bg-red-600 text-white shadow-[0_0_15px_rgba(239,68,68,0.5)] animate-pulse'
                        : 'bg-slate-100 dark:bg-white/10 hover:bg-slate-200 dark:hover:bg-white/20 text-slate-600 dark:text-slate-300'
                    }`}
                    title={isSupported ? t('chat.voiceInput') : t('chat.voiceInputNotSupported')}
                    disabled={!isSupported}
                  >
                    <Mic size={20} />
                  </button>
                )}
                {input.trim() && (
                  <button 
                    onClick={handleSubmit}
                    className="group p-2 bg-primary-500 hover:bg-primary-glow text-white rounded-xl shadow-lg transition-all active:scale-95 hover:-translate-y-0.5"
                  >
                    <ArrowUp size={20} className="transition-transform group-hover:-translate-y-0.5" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
        {isNewChat && (
          <div className="text-center mt-2 pb-1">
            <span className="text-xs text-slate-500">{t('chat.disclaimer')}</span>
          </div>
        )}
      </div>
    </div>
  );
};

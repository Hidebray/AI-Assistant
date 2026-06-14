import React, { useRef, useEffect } from 'react';
import { Calendar, Brain, ListTodo, Sparkles, Mail } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface PromptTemplate {
  id: string;
  title: string;
  description: string;
  prompt: string;
  icon: React.ReactNode;
}

interface PromptLibraryProps {
  onSelect: (prompt: string) => void;
  onClose: () => void;
}

export const PromptLibrary: React.FC<PromptLibraryProps> = ({ onSelect, onClose }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { t } = useTranslation();

  const templates: PromptTemplate[] = [
    {
      id: 'schedule',
      title: t('promptLibrary.schedule.title'),
      description: t('promptLibrary.schedule.desc'),
      prompt: t('promptLibrary.schedule.prompt'),
      icon: <Calendar size={18} className="text-blue-500" />
    },
    {
      id: 'memory',
      title: t('promptLibrary.memory.title'),
      description: t('promptLibrary.memory.desc'),
      prompt: t('promptLibrary.memory.prompt'),
      icon: <Brain size={18} className="text-purple-500" />
    },
    {
      id: 'task',
      title: t('promptLibrary.task.title'),
      description: t('promptLibrary.task.desc'),
      prompt: t('promptLibrary.task.prompt'),
      icon: <ListTodo size={18} className="text-green-500" />
    },
    {
      id: 'query',
      title: t('promptLibrary.query.title'),
      description: t('promptLibrary.query.desc'),
      prompt: t('promptLibrary.query.prompt'),
      icon: <Sparkles size={18} className="text-amber-500" />
    },
    {
      id: 'email_check',
      title: t('promptLibrary.email_check.title'),
      description: t('promptLibrary.email_check.desc'),
      prompt: t('promptLibrary.email_check.prompt'),
      icon: <Mail size={18} className="text-red-500" />
    }
  ];

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  return (
    <div 
      ref={containerRef}
      className="absolute bottom-full left-0 mb-4 w-72 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl shadow-xl z-50 overflow-hidden flex flex-col transform transition-all animate-in fade-in slide-in-from-bottom-4"
    >
      <div className="p-3 border-b border-slate-100 dark:border-white/5 bg-slate-50/50 dark:bg-black/20">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-white flex items-center gap-2">
          <Sparkles size={16} className="text-amber-500" />
          {t('promptLibrary.title')}
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          {t('promptLibrary.subtitle')}
        </p>
      </div>
      
      <div className="p-2 flex flex-col gap-1 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-white/10">
        {templates.map((t) => (
          <button
            key={t.id}
            onClick={() => onSelect(t.prompt)}
            className="flex items-start gap-3 p-2 w-full text-left rounded-xl hover:bg-slate-100 dark:hover:bg-white/10 transition-colors group"
          >
            <div className="p-2 rounded-lg bg-white dark:bg-black/20 shadow-sm border border-slate-100 dark:border-white/5 shrink-0 group-hover:scale-105 transition-transform">
              {t.icon}
            </div>
            <div>
              <div className="text-sm font-medium text-slate-800 dark:text-slate-200">{t.title}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">{t.description}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

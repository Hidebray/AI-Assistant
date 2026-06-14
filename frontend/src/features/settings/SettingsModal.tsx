import React, { useRef, useEffect } from 'react';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { SettingsSidebar } from './SettingsSidebar';
import { GeneralSettings } from './GeneralSettings';
import { LLMProviderSettings } from './LLMProviderSettings';
import { PluginManagerUI } from './PluginManagerUI';
import gsap from 'gsap';
import { X } from 'lucide-react';

export const SettingsModal: React.FC = () => {
  const { isSettingsOpen, setSettingsOpen, activeTab } = useSettingsStore();
  const overlayRef = useRef<HTMLDivElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isSettingsOpen) {
      gsap.fromTo(overlayRef.current, { opacity: 0 }, { opacity: 1, duration: 0.3 });
      gsap.fromTo(modalRef.current, { scale: 0.95, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "power2.out" });
    }
  }, [isSettingsOpen]);

  const close = () => {
    gsap.to(modalRef.current, { scale: 0.95, opacity: 0, duration: 0.2, ease: "power2.in" });
    gsap.to(overlayRef.current, { 
      opacity: 0, duration: 0.2, 
      onComplete: () => setSettingsOpen(false) 
    });
  };

  if (!isSettingsOpen) return null;

  return (
    <div ref={overlayRef} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 md:p-8">
      <div ref={modalRef} className="w-full max-w-5xl h-[80vh] flex flex-row bg-white/90 dark:bg-slate-900/80 backdrop-blur-3xl border border-slate-200 dark:border-white/20 rounded-2xl shadow-2xl overflow-hidden relative">
        <button onClick={close} className="absolute top-4 right-4 z-20 p-2 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-black/20 hover:bg-slate-200 dark:hover:bg-white/10 rounded-full transition-colors">
          <X size={20} />
        </button>
        
        <SettingsSidebar />
        
        <div className="flex-1 h-full overflow-y-auto p-8 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-white/10">
          {activeTab === 'general' && <GeneralSettings />}
          {activeTab === 'llm' && <LLMProviderSettings />}
          {activeTab === 'plugins' && <PluginManagerUI />}
        </div>
      </div>
    </div>
  );
};

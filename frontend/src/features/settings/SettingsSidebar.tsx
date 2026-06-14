import React from 'react';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { Settings, Cpu, Puzzle } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import { useTranslation } from 'react-i18next';

type SettingsTab = 'general' | 'llm' | 'plugins';

export const SettingsSidebar: React.FC = () => {
  const { t } = useTranslation();
  const { activeTab, setActiveTab } = useSettingsStore();

  const tabs = [
    { id: 'general' as SettingsTab, label: t('settings.tabs.general'), icon: Settings },
    { id: 'llm' as SettingsTab, label: t('settings.tabs.llm'), icon: Cpu },
    { id: 'plugins' as SettingsTab, label: t('settings.tabs.plugins'), icon: Puzzle },
  ];

  return (
    <div className="w-64 h-full border-r border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-black/20 p-4 flex flex-col shrink-0 transition-colors">
      <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6 px-2">{t('settings.title')}</h2>
      
      <div className="flex flex-col gap-1">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={twMerge(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium",
              activeTab === tab.id 
                ? "bg-primary-50 dark:bg-primary-500/20 text-primary-700 dark:text-primary-400" 
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-white/5"
            )}
          >
            <tab.icon size={18} />
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
};

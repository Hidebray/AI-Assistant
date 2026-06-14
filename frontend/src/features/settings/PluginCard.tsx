import React, { useState } from 'react';
import { Settings } from 'lucide-react';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { useTranslation } from 'react-i18next';

export interface PluginProps {
  id: string;
  name: string;
  version: string;
  source: string;
  description: string;
  isActive: boolean;
  hasConfig: boolean;
  onToggle?: (id: string, newState: boolean) => Promise<void> | void;
  onOpenConfig?: (id: string) => void;
}

export const PluginCard: React.FC<PluginProps> = (props) => {
  const { t } = useTranslation();
  const [isActive, setIsActive] = useState(props.isActive);
  const [loading, setLoading] = useState(false);
  const addToast = useSettingsStore(state => state.addToast);

  // Fallback to props.name/description if translation is not found
  const pluginName = t(`settings.plugins.items.${props.id}.name`, { defaultValue: props.name });
  const pluginDesc = t(`settings.plugins.items.${props.id}.description`, { defaultValue: props.description });

  const handleToggle = async () => {
    if (loading) return;
    setLoading(true);
    if (props.onToggle) {
        await props.onToggle(props.id, !isActive);
        setIsActive(!isActive);
    } else {
        // Simulate API Call
        await new Promise(r => setTimeout(r, 500));
        setIsActive(!isActive);
        addToast(`Đã ${!isActive ? 'bật' : 'tắt'} plugin ${props.name}`);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col justify-between p-5 min-h-[160px] bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl hover:bg-slate-100 dark:hover:bg-white/10 transition-colors shadow-sm dark:shadow-none group">
      
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-3 flex-1 min-w-0 pr-4">
          <div className="w-10 h-10 shrink-0 rounded-lg bg-primary-50 dark:bg-primary-500/20 flex items-center justify-center text-primary-600 dark:text-primary-400 text-lg">
            🧩
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-slate-900 dark:text-slate-100 truncate" title={pluginName}>{pluginName}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{props.version} • {props.source}</p>
          </div>
        </div>
        
        <button 
          onClick={handleToggle}
          disabled={loading}
          className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${isActive ? 'bg-primary-500' : 'bg-slate-300 dark:bg-slate-600'} ${loading ? 'opacity-50' : ''}`}
        >
          <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isActive ? 'translate-x-6' : 'translate-x-1'} shadow-sm`} />
        </button>
      </div>

      <p className="text-sm text-slate-600 dark:text-slate-300 mt-3 line-clamp-2 leading-relaxed">
        {pluginDesc}
      </p>

      {props.hasConfig ? (
        <div className="mt-2 flex justify-end">
          <button onClick={() => props.onOpenConfig?.(props.id)} className="flex items-center gap-1 text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors">
            <Settings size={14} /> {t('settings.plugins.config')}
          </button>
        </div>
      ) : (
        <div className="mt-2 h-4" /> // placeholder
      )}
    </div>
  );
};

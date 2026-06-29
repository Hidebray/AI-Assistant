import React, { useCallback, useState, useEffect } from 'react';
import { PluginCard, type PluginProps } from './PluginCard';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { useAuthStore } from '../../core/store/useAuthStore';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const PluginManagerUI: React.FC = () => {
  const [plugins, setPlugins] = useState<PluginProps[]>([]);
  const [loading, setLoading] = useState(true);
  const addToast = useSettingsStore(state => state.addToast);
  const token = useAuthStore(state => state.token);
  const { t } = useTranslation();

  const fetchPlugins = useCallback(async () => {
    try {
      setLoading(true);
      const headers: Record<string, string> = {};
      if (token) headers.Authorization = `Bearer ${token}`;
      const res = await fetch('http://localhost:8000/api/settings', { headers });
      if (res.ok) {
        const data = await res.json();
        // Server returns plugin in `data.plugins`
        setPlugins(data.plugins || []);
      }
    } catch (e) {
      console.error("Failed to fetch plugins", e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      fetchPlugins();
    }, 0);
    return () => window.clearTimeout(timerId);
  }, [fetchPlugins]);

  const handleToggle = async (id: string, newState: boolean) => {
    // Optimistic update
    setPlugins(prev => prev.map(p => p.id === id ? { ...p, isActive: newState } : p));
    
    try {
      const payload: Record<string, boolean> = {};
      payload[`plugins.${id}.active`] = newState;
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers.Authorization = `Bearer ${token}`;
      
      const res = await fetch('http://localhost:8000/api/settings', {
        method: 'PUT',
        headers,
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const pluginName = t(`settings.plugins.items.${id}.name`, { defaultValue: plugins.find(p => p.id === id)?.name || id });
        addToast(newState ? t('settings.plugins.enabled', { name: pluginName }) : t('settings.plugins.disabled', { name: pluginName }));
      } else {
        // Revert on failure
        setPlugins(prev => prev.map(p => p.id === id ? { ...p, isActive: !newState } : p));
        addToast(t('settings.plugins.saveError'));
      }
    } catch (e) {
      console.error(e);
      setPlugins(prev => prev.map(p => p.id === id ? { ...p, isActive: !newState } : p));
    }
  };

  const handleOpenConfig = async (id: string) => {
    if (id === 'calendar_plugin' || id === 'email_plugin') {
      try {
        // For Google OAuth plugins
        const headers: Record<string, string> = {};
        if (token) headers.Authorization = `Bearer ${token}`;
        
        addToast(t('settings.plugins.googleInit'));
        const res = await fetch('http://localhost:8000/api/google/auth', {
          method: 'POST',
          headers
        });
        
        if (res.ok) {
          const data = await res.json();
          addToast(data.message || t('settings.plugins.googleCheckBrowser'));
        } else {
          addToast(t('settings.plugins.googleMissingCreds'));
        }
      } catch (e) {
        addToast(t('settings.plugins.serverError'));
      }
    } else {
      const pluginName = t(`settings.plugins.items.${id}.name`, { defaultValue: plugins.find(p => p.id === id)?.name || id });
      addToast(t('settings.plugins.configUnderDev', { name: pluginName }));
    }
  };

  if (loading) {
    return <div className="w-full flex justify-center py-20 text-slate-500 dark:text-slate-400"><Loader2 className="animate-spin" size={32} /></div>;
  }

  return (
    <div className="w-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">{t('settings.plugins.title')}</h2>
        <p className="text-slate-500 dark:text-slate-400 text-sm">{t('settings.plugins.description')}</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {plugins.length === 0 ? (
          <p className="text-slate-500 italic col-span-full">{t('settings.plugins.noPlugins')}</p>
        ) : (
          plugins.map(plugin => (
            <PluginCard 
              key={plugin.id} 
              {...plugin} 
              onToggle={handleToggle}
              onOpenConfig={handleOpenConfig}
            />
          ))
        )}
      </div>
    </div>
  );
};

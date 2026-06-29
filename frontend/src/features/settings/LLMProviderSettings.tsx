import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useSettingsSync } from './useSettingsSync';
import { useAuthStore } from '../../core/store/useAuthStore';

interface LLMFormValues {
  openaiKey: string;
  geminiKey: string;
  ollamaBaseUrl: string;
  systemPrompt: string;
}

export const LLMProviderSettings: React.FC = () => {
  const { t } = useTranslation();
  const [showOpenAI, setShowOpenAI] = useState(false);
  const [showGemini, setShowGemini] = useState(false);
  const [showAdvancedOllama, setShowAdvancedOllama] = useState(false);
  const [loading, setLoading] = useState(true);
  const token = useAuthStore(state => state.token);
  
  const { register, watch, reset } = useForm<LLMFormValues>({
    defaultValues: {
      openaiKey: '',
      geminiKey: '',
      ollamaBaseUrl: '',
      systemPrompt: ''
    }
  });

  const [ollamaStatus, setOllamaStatus] = useState<any>(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const headers: Record<string, string> = {};
        if (token) headers.Authorization = `Bearer ${token}`;
        const response = await fetch('http://localhost:8000/api/settings', { headers });
        if (response.ok) {
          const data = await response.json();
          reset({
            openaiKey: data.llm?.openaiKey || '',
            geminiKey: data.llm?.geminiKey || '',
            ollamaBaseUrl: data.llm?.ollamaBaseUrl || 'http://localhost:11434',
            systemPrompt: data.llm?.systemPrompt || ''
          });
        }
      } catch (e) {
        console.error("Failed to load settings", e);
      } finally {
        setLoading(false);
      }
    };

    const fetchOllamaStatus = async () => {
      try {
        const headers: Record<string, string> = {};
        if (token) headers.Authorization = `Bearer ${token}`;
        const statusResponse = await fetch('http://localhost:8000/api/ollama/status', { headers });
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setOllamaStatus(statusData);
        }
      } catch (e) {
        console.error("Failed to load Ollama status", e);
      }
    };

    fetchSettings();
    fetchOllamaStatus();
  }, [reset, token]);

  const formData = watch();
  
  // Custom hook will automatically debounce and PUT changes
  useSettingsSync(loading ? null : formData);

  if (loading) {
    return <div className="w-full flex justify-center py-20 text-slate-500 dark:text-slate-400"><Loader2 className="animate-spin" size={32} /></div>;
  }

  return (
    <div className="w-full max-w-2xl text-slate-900 dark:text-white">
      <h2 className="text-2xl font-bold mb-6">{t('settings.llm.title')}</h2>
      
      <div className="space-y-6">
        {/* OpenAI */}
        <div className="bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary-500/10 blur-3xl rounded-full -mr-10 -mt-10 pointer-events-none"></div>
          <h3 className="font-semibold mb-1 text-slate-800 dark:text-slate-100">{t('settings.llm.openaiKey')}</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">{t('settings.llm.openaiKeyDesc')}</p>
          
          <div className="relative">
            <input 
              type={showOpenAI ? "text" : "password"}
              {...register('openaiKey')}
              className="w-full h-11 pl-4 pr-12 bg-transparent border border-slate-300 dark:border-white/10 rounded-lg text-slate-900 dark:text-slate-200 outline-none focus:border-primary-500 transition-colors"
              placeholder={t('settings.llm.placeholderKey')}
            />
            <button 
              onClick={() => setShowOpenAI(!showOpenAI)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors"
            >
              {showOpenAI ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        {/* Gemini */}
        <div className="bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 blur-3xl rounded-full -mr-10 -mt-10 pointer-events-none"></div>
          <h3 className="font-semibold mb-1 text-slate-800 dark:text-slate-100">{t('settings.llm.geminiKey')}</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">{t('settings.llm.geminiKeyDesc')}</p>
          
          <div className="relative">
            <input 
              type={showGemini ? "text" : "password"}
              {...register('geminiKey')}
              className="w-full h-11 pl-4 pr-12 bg-transparent border border-slate-300 dark:border-white/10 rounded-lg text-slate-900 dark:text-slate-200 outline-none focus:border-blue-500 transition-colors"
              placeholder={t('settings.llm.placeholderKey')}
            />
            <button 
              onClick={() => setShowGemini(!showGemini)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors"
            >
              {showGemini ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        {/* Ollama Local */}
        <div className="bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 blur-3xl rounded-full -mr-10 -mt-10 pointer-events-none"></div>
          <div className="flex justify-between items-start mb-1">
            <h3 className="font-semibold text-slate-800 dark:text-slate-100">{t('settings.llm.ollamaTitle')}</h3>
            {ollamaStatus && (
              <div className={`flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${ollamaStatus.server_running ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'}`}>
                <div className={`w-2 h-2 rounded-full ${ollamaStatus.server_running ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                {ollamaStatus.server_running ? 'Online' : (ollamaStatus.installed ? 'Offline' : 'Not Installed')}
              </div>
            )}
          </div>
          
          {ollamaStatus?.server_running && ollamaStatus.models?.length > 0 ? (
            <div className="text-sm text-slate-600 dark:text-slate-300 mt-2 mb-4">
              <span className="font-medium">{t('settings.llm.installedModels')}:</span> {ollamaStatus.models.join(', ')}
            </div>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 mb-4">
              {t('settings.llm.ollamaAutoConnDesc')}
            </p>
          )}

          <button
            type="button"
            onClick={() => setShowAdvancedOllama(!showAdvancedOllama)}
            className="text-xs text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300 font-medium transition-colors mb-2"
          >
            {showAdvancedOllama ? t('settings.llm.collapse') : t('settings.llm.advanced')}
          </button>

          {showAdvancedOllama && (
            <div className="mt-2 pt-4 border-t border-slate-200 dark:border-white/10">
              <h4 className="text-sm font-medium mb-1 text-slate-800 dark:text-slate-200">{t('settings.llm.ollamaUrl')}</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">{t('settings.llm.ollamaUrlDesc')}</p>
              
              <input 
                type="text"
                {...register('ollamaBaseUrl')}
                className="w-full h-11 px-4 bg-transparent border border-slate-300 dark:border-white/10 rounded-lg text-slate-900 dark:text-slate-200 outline-none focus:border-green-500 transition-colors"
                placeholder="http://localhost:11434"
              />
            </div>
          )}
        </div>
        {/* System Prompt */}
        <div className="bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-5">
          <h3 className="font-semibold mb-1 text-slate-800 dark:text-slate-100">{t('settings.llm.systemPrompt')}</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">{t('settings.llm.systemPromptDesc')}</p>
          
          <textarea 
            {...register('systemPrompt')}
            className="w-full h-32 p-4 bg-transparent border border-slate-300 dark:border-white/10 rounded-lg text-slate-900 dark:text-slate-200 outline-none focus:border-primary-500 transition-colors resize-y text-sm"
            placeholder={t('settings.llm.placeholderSystemPrompt')}
          />
        </div>
      </div>
    </div>
  );
};

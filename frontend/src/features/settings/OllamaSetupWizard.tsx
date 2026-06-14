import React, { useState, useEffect } from 'react';
import { Loader2, Download, CheckCircle2, ChevronRight, X, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '../../core/store/useAuthStore';
import { useTranslation } from 'react-i18next';

interface OllamaStatus {
  installed: boolean;
  server_running: boolean;
  models: string[];
  recommended_model: string;
  ollama_path: string | null;
}

interface OllamaSetupWizardProps {
  onComplete: () => void;
  onSkip: () => void;
  initialStatus?: OllamaStatus;
}

export const OllamaSetupWizard: React.FC<OllamaSetupWizardProps> = ({ onComplete, onSkip, initialStatus }) => {
  const token = useAuthStore(state => state.token);
  
  const { t } = useTranslation();
  
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [status, setStatus] = useState<OllamaStatus | null>(initialStatus || null);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState(t('wizard.statusInit'));
  const [error, setError] = useState<string | null>(null);

  // 1. Initial Status Check (if not provided)
  useEffect(() => {
    if (status) {
      evaluateStatus(status);
      return;
    }

    const checkStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/ollama/status', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setStatus(data);
          evaluateStatus(data);
        } else {
          setError(t('wizard.errorConnBackend'));
        }
      } catch (e) {
        setError(t('wizard.errorConnGeneric'));
      }
    };
    checkStatus();
  }, [status, token]);

  const evaluateStatus = (currentStatus: OllamaStatus) => {
    if (!currentStatus.installed) {
      setStep(2); // Cần cài đặt
    } else if (currentStatus.models.length === 0) {
      setStep(3); // Cần tải model
    } else {
      setStep(4); // Đã sẵn sàng
    }
  };

  // 2. Install Handler
  const handleInstall = async () => {
    setError(null);
    setProgress(0);
    setStatusText(t('wizard.statusConnOllama'));
    
    try {
      const response = await fetch('http://localhost:8000/api/ollama/install', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!response.body) throw new Error('No readable stream');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim();
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              if (data.stage === 'downloading') {
                setProgress(data.progress);
                setStatusText(`${t('wizard.statusDownloading')} ${data.downloaded_mb}MB / ${data.total_mb}MB (${data.progress}%)`);
              } else if (data.stage === 'installing') {
                setProgress(100);
                setStatusText(data.message || t('wizard.statusInstalling'));
              } else if (data.stage === 'starting_server' || data.stage === 'server_started') {
                setStatusText(data.message);
              } else if (data.stage === 'error') {
                setError(data.message);
                return;
              } else if (data.stage === 'stream_end') {
                // Done installing, move to pull model
                setStep(3);
                return;
              }
            } catch (e) {
              console.error('JSON parse error in stream', dataStr);
            }
          }
        }
      }
    } catch (e: any) {
      setError(e.message || t('wizard.errorInstall'));
    }
  };

  // 3. Pull Model Handler
  const handlePullModel = async () => {
    setError(null);
    setProgress(0);
    setStatusText(t('wizard.statusPrepModel'));
    const targetModel = status?.recommended_model || 'qwen2.5:3b';
    
    try {
      const response = await fetch('http://localhost:8000/api/ollama/pull', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ model: targetModel })
      });
      
      if (!response.body) throw new Error('No readable stream');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim();
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              if (data.stage === 'pulling') {
                setProgress(data.progress);
                setStatusText(`${t('wizard.statusPulling')} ${data.status} (${data.completed_mb}MB / ${data.total_mb}MB) - ${data.progress}%`);
              } else if (data.stage === 'pull_complete') {
                setProgress(100);
                setStatusText(t('wizard.statusPullComplete'));
              } else if (data.stage === 'error') {
                setError(data.message);
                return;
              } else if (data.stage === 'stream_end') {
                setStep(4);
                return;
              }
            } catch (e) {
              // Ignore partial JSON chunks
            }
          }
        }
      }
    } catch (e: any) {
      setError(e.message || t('wizard.errorPull'));
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center z-50 p-6">
      <div className="max-w-xl w-full bg-white dark:bg-slate-900 rounded-2xl shadow-xl overflow-hidden border border-slate-200 dark:border-white/10">
        
        {/* Header */}
        <div className="px-8 py-6 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center text-primary-600 dark:text-primary-400">
              <Download size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800 dark:text-white">{t('wizard.headerTitle')}</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">{t('wizard.headerDesc')}</p>
            </div>
          </div>
          <button 
            onClick={onSkip}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors"
            title={t('wizard.btnSkipTitle')}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl flex items-start gap-3 text-red-600 dark:text-red-400">
              <AlertTriangle size={20} className="shrink-0 mt-0.5" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          {step === 1 && (
            <div className="flex flex-col items-center py-10">
              <Loader2 size={40} className="animate-spin text-primary-500 mb-4" />
              <p className="text-slate-600 dark:text-slate-300 font-medium">{statusText}</p>
            </div>
          )}

          {step === 2 && (
            <div className="flex flex-col items-center text-center">
              <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-2">{t('wizard.step2Title')}</h3>
              <p className="text-slate-600 dark:text-slate-400 mb-8 max-w-md">
                {t('wizard.step2Desc')}
              </p>
              
              {progress > 0 ? (
                <div className="w-full">
                  <div className="flex justify-between text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    <span>{statusText}</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary-500 transition-all duration-300 ease-out"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              ) : (
                <button 
                  onClick={handleInstall}
                  className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-xl transition-colors flex items-center gap-2"
                >
                  <Download size={18} />
                  {t('wizard.btnInstall')}
                </button>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400 flex items-center justify-center mb-4">
                <CheckCircle2 size={32} />
              </div>
              <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-2">{t('wizard.step3Title')}</h3>
              <p className="text-slate-600 dark:text-slate-400 mb-8 max-w-md">
                {t('wizard.step3Desc1')}<strong className="text-primary-600 dark:text-primary-400">{status?.recommended_model}</strong> (~1.9GB).
              </p>
              
              {progress > 0 ? (
                <div className="w-full">
                  <div className="flex justify-between text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    <span>{statusText}</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary-500 transition-all duration-300 ease-out"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-3">{t('wizard.step3Desc2')}</p>
                </div>
              ) : (
                <button 
                  onClick={handlePullModel}
                  className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-xl transition-colors flex items-center gap-2"
                >
                  <Download size={18} />
                  {t('wizard.btnPull')}{status?.recommended_model}
                </button>
              )}
            </div>
          )}

          {step === 4 && (
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-green-400 to-primary-500 flex items-center justify-center text-white mb-6 shadow-lg shadow-primary-500/30">
                <CheckCircle2 size={40} />
              </div>
              <h3 className="text-2xl font-bold text-slate-800 dark:text-white mb-2">{t('wizard.step4Title')}</h3>
              <p className="text-slate-600 dark:text-slate-400 mb-8 max-w-md">
                {t('wizard.step4Desc')}
              </p>
              
              <button 
                onClick={onComplete}
                className="px-8 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold rounded-xl transition-transform hover:scale-105 flex items-center gap-2"
              >
                {t('wizard.btnStart')} <ChevronRight size={18} />
              </button>
            </div>
          )}

        </div>
        
        {/* Footer */}
        {step < 4 && (
          <div className="px-8 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-white/5 flex justify-center">
            <button 
              onClick={onSkip}
              className="text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-colors underline underline-offset-4"
            >
              {t('wizard.btnSkipText')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

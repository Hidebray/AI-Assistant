import React, { useEffect, useState } from 'react';
import { AuthLayout } from '../features/auth/AuthLayout';
import { MainLayout } from '../features/layout/MainLayout';
import { SpotlightSearch } from '../features/overlays/SpotlightSearch';
import { useAuthStore } from '../core/store/useAuthStore';
import { OllamaSetupWizard } from '../features/settings/OllamaSetupWizard';

declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
  }
}

const getInitialWindowLabel = () => {
  const params = new URLSearchParams(window.location.search);
  return params.get('window') || 'main';
};

const App: React.FC = () => {
  const token = useAuthStore(state => state.token);
  const [windowLabel, setWindowLabel] = useState(getInitialWindowLabel);

  useEffect(() => {
    // Check Tauri Window Label if running in Tauri
    if (!window.location.search && window.__TAURI_INTERNALS__) {
      import('@tauri-apps/api/webviewWindow').then(module => {
        const currentWindow = module.getCurrentWebviewWindow();
        if (currentWindow && currentWindow.label) {
          setWindowLabel(currentWindow.label);
        }
      }).catch(console.error);
    }
  }, []);

  const [showWizard, setShowWizard] = useState(false);
  const [wizardStatus, setWizardStatus] = useState<any>(null);

  // Check Ollama status after login
  useEffect(() => {
    if (!token) return;
    
    // If user previously skipped the wizard, don't show it again
    if (localStorage.getItem('aaa_skip_ollama_setup') === 'true') {
      return;
    }

    const checkStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/ollama/status', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          // If not installed, or no models, show wizard
          if (!data.installed || data.models.length === 0) {
            setWizardStatus(data);
            setShowWizard(true);
          }
        }
      } catch (e) {
        console.error("Failed to check Ollama status", e);
      }
    };
    
    checkStatus();
  }, [token]);

  const handleWizardComplete = () => {
    setShowWizard(false);
    localStorage.setItem('aaa_skip_ollama_setup', 'true');
  };

  const handleWizardSkip = () => {
    setShowWizard(false);
    localStorage.setItem('aaa_skip_ollama_setup', 'true');
  };

  if (windowLabel === 'spotlight') {
    return <SpotlightSearch />;
  }

  return (
    <>
      {!token ? (
        <AuthLayout onLoginSuccess={() => undefined} />
      ) : showWizard ? (
        <OllamaSetupWizard 
          onComplete={handleWizardComplete} 
          onSkip={handleWizardSkip}
          initialStatus={wizardStatus}
        />
      ) : (
        <MainLayout />
      )}
    </>
  );
};

export default App;

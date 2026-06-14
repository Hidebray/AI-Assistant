import React, { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import gsap from 'gsap';
import { AlertCircle } from 'lucide-react';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';
import { useAlertStore } from '../../core/store/useAlertStore';

export const NativeToastContainer: React.FC = () => {
  const currentAlert = useAlertStore(state => state.currentAlert);
  const clearAlert = useAlertStore(state => state.clearAlert);
  const toastRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (currentAlert && toastRef.current) {
      const appWindow = getCurrentWebviewWindow();
      appWindow.show();
      gsap.fromTo(toastRef.current,
        { x: '100%', opacity: 0 },
        { x: '0%', opacity: 1, duration: 0.5, ease: "power3.out" }
      );
    }
  }, [currentAlert]);

  const handleAction = async () => {
    gsap.to(toastRef.current, { 
      x: '100%', opacity: 0, duration: 0.3, ease: "power2.in",
      onComplete: async () => {
        clearAlert();
        await getCurrentWebviewWindow().hide();
      }
    });
  };

  if (!currentAlert) return null;

  const bgBorderColor = currentAlert.urgency === 'critical' ? 'border-red-500/50' : currentAlert.urgency === 'high' ? 'border-amber-500/50' : 'border-white/20';
  const iconColor = currentAlert.urgency === 'critical' ? 'text-red-500' : currentAlert.urgency === 'high' ? 'text-amber-500' : 'text-slate-400';

  return (
    <div className="w-full h-screen flex flex-col justify-end items-end p-4 bg-transparent overflow-hidden">
      <div 
        ref={toastRef} 
        className={`w-80 bg-slate-900/90 backdrop-blur-3xl border shadow-2xl rounded-xl p-4 pointer-events-auto flex flex-col gap-2 shrink-0 ${bgBorderColor}`}
      >
        <div className="flex items-start gap-3">
          <div className={`mt-1 shrink-0 ${iconColor}`}>
            <AlertCircle size={20} />
          </div>
          <div className="flex-1">
            <h4 className="text-white font-bold text-sm mb-1">{currentAlert.title}</h4>
            <p className="text-slate-300 text-xs leading-relaxed">{currentAlert.message}</p>
          </div>
        </div>
        
        <div className="flex justify-end gap-2 mt-2">
          <button 
            onClick={handleAction}
            className="px-3 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:bg-white/10 transition-colors"
          >
            Bỏ qua
          </button>
          <button 
            onClick={handleAction}
            className="px-3 py-1.5 rounded-md text-xs font-medium bg-primary-500 hover:bg-primary-600 text-white transition-colors shadow-lg shadow-primary-500/20"
          >
            Tham gia ngay
          </button>
        </div>
      </div>
    </div>
  );
};

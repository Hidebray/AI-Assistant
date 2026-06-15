import React, { useRef } from 'react';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { useGSAP } from '@gsap/react';
import gsap from 'gsap';
import { Check, AlertTriangle, Info } from 'lucide-react';

const ToastMessage: React.FC<{ message: string, id: string }> = ({ message }) => {
  const elRef = useRef<HTMLDivElement>(null);
  
  useGSAP(() => {
    if (elRef.current) {
      gsap.fromTo(elRef.current, 
        { y: -50, opacity: 0 }, 
        { y: 0, opacity: 1, duration: 0.4, ease: "back.out(1.5)" }
      );
    }
  }, []);

  let icon = <Check size={14} />;
  let colorClass = "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400";
  let borderClass = "border-slate-200 bg-white/90 dark:border-white/10 dark:bg-slate-800/90 text-slate-800 dark:text-slate-100";
  let displayMessage = message;

  if (message.startsWith("[CRITICAL]")) {
    icon = <AlertTriangle size={14} />;
    colorClass = "bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400";
    borderClass = "border-red-200 bg-red-50/90 dark:border-red-500/30 dark:bg-red-950/90 text-red-900 dark:text-red-100";
    displayMessage = message.replace("[CRITICAL] ", "");
  } else if (message.startsWith("[HIGH]")) {
    icon = <Info size={14} />;
    colorClass = "bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400";
    borderClass = "border-amber-200 bg-amber-50/90 dark:border-amber-500/30 dark:bg-amber-950/90 text-amber-900 dark:text-amber-100";
    displayMessage = message.replace("[HIGH] ", "");
  } else if (message.startsWith("[NORMAL]") || message.startsWith("[LOW]")) {
    displayMessage = message.replace(/\[(NORMAL|LOW)\] /, "");
  }

  return (
    <div ref={elRef} className={`pointer-events-auto flex items-center gap-2.5 border shadow-lg dark:shadow-glass-widget px-4 py-2.5 rounded-2xl text-sm font-medium backdrop-blur-md transition-colors ${borderClass}`}>
      <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 shadow-sm ${colorClass}`}>
        {icon}
      </div>
      {displayMessage}
    </div>
  );
};

export const ToastContainer: React.FC = () => {
  const toasts = useSettingsStore(state => state.toasts);

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 pointer-events-none items-center">
      {toasts.map(toast => (
        <ToastMessage key={toast.id} id={toast.id} message={toast.message} />
      ))}
    </div>
  );
};

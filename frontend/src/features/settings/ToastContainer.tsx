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

  let icon = <Check size={12} />;
  let colorClass = "bg-green-500/20 text-green-400";
  let borderClass = "border-white/10 bg-slate-800";
  let displayMessage = message;

  if (message.startsWith("[CRITICAL]")) {
    icon = <AlertTriangle size={12} />;
    colorClass = "bg-red-500/20 text-red-400";
    borderClass = "border-red-500/30 bg-red-950/90";
    displayMessage = message.replace("[CRITICAL] ", "");
  } else if (message.startsWith("[HIGH]")) {
    icon = <Info size={12} />;
    colorClass = "bg-orange-500/20 text-orange-400";
    borderClass = "border-orange-500/30 bg-orange-950/90";
    displayMessage = message.replace("[HIGH] ", "");
  } else if (message.startsWith("[NORMAL]") || message.startsWith("[LOW]")) {
    displayMessage = message.replace(/\[(NORMAL|LOW)\] /, "");
  }

  return (
    <div ref={elRef} className={`pointer-events-auto flex items-center gap-2 border shadow-glass-widget px-4 py-2 rounded-full text-sm text-slate-100 ${borderClass}`}>
      <div className={`w-5 h-5 rounded-full flex items-center justify-center ${colorClass}`}>
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

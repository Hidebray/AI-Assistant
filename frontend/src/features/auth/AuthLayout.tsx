import React, { useState, useRef, useEffect } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { Sun, Moon } from 'lucide-react';
import { useTranslation } from 'react-i18next';

gsap.registerPlugin(useGSAP);

interface AuthLayoutProps {
  onLoginSuccess?: () => void;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ onLoginSuccess }) => {
  const { i18n } = useTranslation();
  const [isLogin, setIsLogin] = useState(true);
  const [isDark, setIsDark] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const formWrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains('dark'));
  }, []);



  const toggleForm = () => {
    if (!formWrapperRef.current) return;
    
    gsap.to(formWrapperRef.current, {
      opacity: 0,
      x: isLogin ? -30 : 30,
      duration: 0.3,
      ease: "power2.in",
      onComplete: () => {
        setIsLogin(!isLogin);
        gsap.fromTo(formWrapperRef.current, 
          { opacity: 0, x: isLogin ? 30 : -30 },
          { opacity: 1, x: 0, duration: 0.4, ease: "power2.out" }
        );
      }
    });
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-transparent">
      {/* Tauri drag region */}
      <header data-tauri-drag-region className="absolute top-0 left-0 h-10 w-full cursor-move z-50" />

      {/* Top right controls */}
      <div className="absolute top-6 right-6 flex items-center gap-4 z-50">
        {/* Language Switch */}
        <div className="flex items-center p-1 rounded-full bg-white/40 dark:bg-black/40 backdrop-blur-md border border-white/20 shadow-sm">
          <button
            onClick={() => i18n.changeLanguage('en')}
            className={`px-3 py-1.5 text-xs font-bold rounded-full transition-all duration-300 ${i18n.language === 'en' ? 'bg-white text-primary-600 shadow-sm dark:bg-slate-700 dark:text-primary-400' : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'}`}
          >
            EN
          </button>
          <button
            onClick={() => i18n.changeLanguage('vi')}
            className={`px-3 py-1.5 text-xs font-bold rounded-full transition-all duration-300 ${i18n.language === 'vi' ? 'bg-white text-primary-600 shadow-sm dark:bg-slate-700 dark:text-primary-400' : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'}`}
          >
            VI
          </button>
        </div>

        {/* Theme Switch */}
        <div className="flex items-center p-1 rounded-full bg-white/40 dark:bg-black/40 backdrop-blur-md border border-white/20 shadow-sm">
          <button
            onClick={() => {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('app_theme', 'light');
                setIsDark(false);
            }}
            className={`p-1.5 rounded-full transition-all duration-300 ${!isDark ? 'bg-white text-yellow-500 shadow-sm dark:bg-slate-700' : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'}`}
            title="Light Mode"
          >
            <Sun size={16} />
          </button>
          <button
            onClick={() => {
                document.documentElement.classList.add('dark');
                localStorage.setItem('app_theme', 'dark');
                setIsDark(true);
            }}
            className={`p-1.5 rounded-full transition-all duration-300 ${isDark ? 'bg-slate-800 text-blue-400 shadow-sm dark:bg-slate-700 dark:text-blue-300' : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'}`}
            title="Dark Mode"
          >
            <Moon size={16} />
          </button>
        </div>
      </div>

      {/* Auth Card - Level 2 Glass */}
      <div 
        ref={containerRef}
        className="w-full max-w-md bg-white/70 dark:bg-slate-900/40 backdrop-blur-2xl border border-slate-200 dark:border-white/20 shadow-xl dark:shadow-glass-widget rounded-2xl p-8 flex flex-col relative overflow-hidden transition-all duration-500 min-h-[500px]"
      >
        <div ref={formWrapperRef} className="w-full h-full">
          {isLogin ? (
            <LoginForm onToggleForm={toggleForm} onSuccess={onLoginSuccess} />
          ) : (
            <RegisterForm onToggleForm={toggleForm} />
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { AuthInput } from './AuthInput';
import { loginSchema, type LoginFormValues } from '../../core/schemas/auth.schema';
import { useAuth } from './useAuth';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';

interface LoginFormProps {
  onToggleForm: () => void;
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onToggleForm, onSuccess }) => {
  const { t } = useTranslation();
  const { login, isLoading, error } = useAuth();
  const containerRef = useRef<HTMLDivElement>(null);
  
  useGSAP(() => {
    gsap.fromTo(
      ".gsap-animate",
      { y: 30, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, stagger: 0.1, ease: "back.out(1.7)" }
    );
  }, { scope: containerRef });
  
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    try {
      await login(data);
      if (onSuccess) onSuccess();
    } catch {
      // Error handled by hook
    }
  };

  return (
    <div ref={containerRef} className="w-full h-full flex flex-col">
      <div className="mb-8 gsap-animate">
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">{t('auth.login.title')}</h2>
        <p className="text-slate-600 dark:text-slate-400">{t('auth.login.subtitle')}</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/50 rounded-lg text-red-600 dark:text-red-400 text-sm gsap-animate">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-1">
        <div className="gsap-animate">
          <AuthInput
            label={t('auth.login.username')}
            placeholder={t('auth.login.username_placeholder')}
            {...register("username")}
            error={errors.username?.message}
          />
        </div>
        
        <div className="gsap-animate">
          <AuthInput
            label={t('auth.login.password')}
            type="password"
            placeholder={t('auth.login.password_placeholder')}
            {...register("password")}
            error={errors.password?.message}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="mt-6 w-full h-12 bg-primary-500 hover:bg-primary-600 dark:hover:bg-primary-glow text-white font-medium rounded-lg shadow-lg hover:shadow-xl dark:hover:shadow-ai-glow transition-all duration-300 active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {isLoading ? <Loader2 className="animate-spin" /> : t('auth.login.submit')}
        </button>
      </form>

      <div className="mt-8 text-center text-sm text-slate-600 dark:text-slate-400 gsap-animate">
        {t('auth.login.noAccount')}{' '}
        <button 
          type="button"
          onClick={onToggleForm}
          className="text-primary-600 dark:text-primary-500 hover:text-primary-700 dark:hover:text-primary-glow hover:underline transition-colors focus:outline-none font-medium"
        >
          {t('auth.login.signup')}
        </button>
      </div>
    </div>
  );
};

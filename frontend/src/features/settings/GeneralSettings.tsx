import React, { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { useSettingsSync } from './useSettingsSync';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '../../core/store/useAuthStore';
import { useSettingsStore } from '../../core/store/useSettingsStore';

import { useTranslation } from 'react-i18next';
import { enable, disable, isEnabled } from '@tauri-apps/plugin-autostart';
import { isTauri } from '@tauri-apps/api/core';

interface GeneralFormValues {
  theme: string;
  language: string;
  autoStart: boolean;
}

export const GeneralSettings: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [loading, setLoading] = useState(true);
  const token = useAuthStore(state => state.token);
  const logout = useAuthStore(state => state.logout);
  const addToast = useSettingsStore(state => state.addToast);

  const [showResetModal, setShowResetModal] = useState(false);
  const [resetInput, setResetInput] = useState('');
  const [isResetting, setIsResetting] = useState(false);

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const { register, watch, reset, setValue } = useForm<GeneralFormValues>({
    defaultValues: {
      theme: (localStorage.getItem('app_theme') as 'dark' | 'light' | 'system') || 'system',
      language: 'en',
      autoStart: false
    }
  });

  const handleFactoryReset = async () => {
    if (resetInput !== 'DELETE') return;
    setIsResetting(true);
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers.Authorization = `Bearer ${token}`;
      
      const response = await fetch('http://localhost:8000/api/auth/reset', {
        method: 'DELETE',
        headers
      });
      
      if (response.ok) {
        addToast(t("settings.sync.saved"));
        logout();
        window.location.href = "/";
      } else {
        const err = await response.json();
        alert(t('settings.general.dangerZone.failed') + (err.detail || "Unknown error"));
      }
    } catch (e) {
      alert(t('settings.general.dangerZone.failed') + "Connection error");
    } finally {
      setIsResetting(false);
      setShowResetModal(false);
    }
  };

  const handleChangePassword = async () => {
    if (!oldPassword || newPassword.length < 6 || newPassword !== confirmPassword) return;
    setIsChangingPassword(true);
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers.Authorization = `Bearer ${token}`;
      
      const response = await fetch('http://localhost:8000/api/auth/change-password', {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword
        })
      });
      
      if (response.ok) {
        addToast(t('settings.general.account.success'));
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setShowPasswordModal(false);
      } else {
        const err = await response.json();
        let errorMsg = t('settings.general.account.error');
        if (err.detail === 'Incorrect old password') {
          errorMsg = t('settings.general.account.incorrectOldPassword', 'Mật khẩu cũ không đúng');
        }
        addToast("[CRITICAL] " + errorMsg);
      }
    } catch (e) {
      addToast("[CRITICAL] " + t('settings.general.account.error'));
    } finally {
      setIsChangingPassword(false);
    }
  };

  const hasFetched = useRef(false);

  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;

    const fetchSettings = async () => {
      try {
        const headers: Record<string, string> = {};
        if (token) headers.Authorization = `Bearer ${token}`;
        const response = await fetch('http://localhost:8000/api/settings', { headers });
        if (response.ok) {
          const data = await response.json();
          let autostartEnabled = data.general?.autoStart || false;
          
          if (isTauri()) {
            autostartEnabled = await isEnabled();
          }
          
          const savedLang = data.general?.language || 'en';
          i18n.changeLanguage(savedLang);

          reset({
            theme: data.general?.theme || (localStorage.getItem('app_theme') as 'dark' | 'light' | 'system') || 'system',
            language: savedLang,
            autoStart: autostartEnabled
          });
        }
      } catch (e) {
        console.error("Failed to load general settings", e);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const formData = watch();
  
  // Dynamic language update — only triggered by user changing the dropdown
  useEffect(() => {
    if (loading) return; // Prevent flashing default language while fetching
    if (formData.language && formData.language !== i18n.language) {
      i18n.changeLanguage(formData.language);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.language, loading]);

  useSettingsSync(formData);

  // Handle AutoStart Toggle specifically
  const toggleAutoStart = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setValue('autoStart', checked);
    if (isTauri()) {
      try {
        if (checked) {
          await enable();
        } else {
          await disable();
        }
      } catch (err) {
        console.error("Failed to toggle autostart", err);
      }
    }
  };

  // Apply theme dynamically to document when changed
  useEffect(() => {
    if (loading) return; // Prevent flashing default language while fetching
    const root = window.document.documentElement;
    if (formData.theme) {
      localStorage.setItem('app_theme', formData.theme);
    }
    
    if (formData.theme === 'dark') {
      root.classList.add('dark');
    } else if (formData.theme === 'light') {
      root.classList.remove('dark');
    } else {
      // System
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  }, [formData.theme, loading]);

  if (loading) {
    return <div className="w-full flex justify-center py-20 text-slate-400"><Loader2 className="animate-spin" size={32} /></div>;
  }

  return (
    <div className="w-full max-w-2xl text-slate-900 dark:text-white">
      <h2 className="text-2xl font-bold mb-6">{t('settings.general.title')}</h2>
      
      <div className="space-y-6">
        {/* Theme */}
        <div className="bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-5">
          <h3 className="font-semibold mb-1 text-slate-900 dark:text-slate-100">{t('settings.general.theme.label')}</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">{t('settings.general.theme.description')}</p>
          
          <select 
            {...register('theme')}
            className="w-full h-11 px-4 bg-transparent border border-slate-300 dark:border-white/10 rounded-lg text-slate-900 dark:text-slate-200 outline-none focus:border-primary-500 transition-colors"
          >
            <option value="dark" className="text-black">{t('settings.general.theme.dark')}</option>
            <option value="light" className="text-black">{t('settings.general.theme.light')}</option>
            <option value="system" className="text-black">{t('settings.general.theme.system')}</option>
          </select>
        </div>

        {/* Language */}
        <div className="bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-5">
          <h3 className="font-semibold mb-1 text-slate-900 dark:text-slate-100">{t('settings.general.language.label')}</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">{t('settings.general.language.description')}</p>
          
          <select 
            {...register('language')}
            className="w-full h-11 px-4 bg-transparent border border-slate-300 dark:border-white/10 rounded-lg text-slate-900 dark:text-slate-200 outline-none focus:border-primary-500 transition-colors"
          >
            <option value="en" className="text-black">English</option>
            <option value="vi" className="text-black">Tiếng Việt</option>
          </select>
        </div>

        {/* Auto-Start */}
        <div className="bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-5">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100">{t('settings.general.autoStart.label')}</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{t('settings.general.autoStart.description')}</p>
            </div>
            
            <label className="relative inline-flex h-6 w-11 items-center rounded-full cursor-pointer">
              <input 
                type="checkbox"
                {...register('autoStart', {
                  onChange: toggleAutoStart
                })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-300 dark:bg-slate-600 rounded-full peer peer-checked:bg-primary-500 transition-colors"></div>
              <span className="absolute left-1 top-1 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-5 shadow-sm"></span>
            </label>
          </div>
        </div>

        {/* Account Security */}
        <div className="bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl p-5">
          <h3 className="font-semibold mb-1 text-slate-900 dark:text-slate-100">{t('settings.general.account.title')}</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">{t('settings.general.account.description')}</p>
          
          <button
            onClick={() => setShowPasswordModal(true)}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-white/10 dark:hover:bg-white/20 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium transition-colors"
          >
            {t('settings.general.account.updatePassword')}
          </button>
        </div>

        {/* Danger Zone */}
        <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-5 mt-8">
          <h3 className="font-semibold mb-1 text-red-600 dark:text-red-400">{t('settings.general.dangerZone.title')}</h3>
          <p className="text-xs text-red-500/80 dark:text-red-300/80 mb-4">{t('settings.general.dangerZone.description')}</p>
          
          <button
            onClick={() => setShowResetModal(true)}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {t('settings.general.dangerZone.factoryReset')}
          </button>
        </div>

      </div>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 max-w-md w-full border border-slate-200 dark:border-slate-700 shadow-2xl">
            <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-2">{t('settings.general.account.updatePassword')}</h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 mb-6">
              {t('settings.general.account.description')}
            </p>
            
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  {t('settings.general.account.oldPassword')}
                </label>
                <input
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  className="w-full h-10 px-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-slate-100 outline-none focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  {t('settings.general.account.newPassword')}
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full h-10 px-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-slate-100 outline-none focus:border-primary-500"
                />
                {newPassword.length > 0 && newPassword.length < 6 && (
                  <p className="text-xs text-red-500 mt-1">{t('settings.general.account.passwordTooShort')}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  {t('settings.general.account.confirmPassword')}
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full h-10 px-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-slate-100 outline-none focus:border-primary-500"
                />
                {confirmPassword.length > 0 && confirmPassword !== newPassword && (
                  <p className="text-xs text-red-500 mt-1">{t('settings.general.account.passwordsNotMatch')}</p>
                )}
              </div>
            </div>
            
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowPasswordModal(false);
                  setOldPassword('');
                  setNewPassword('');
                  setConfirmPassword('');
                }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                disabled={isChangingPassword}
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleChangePassword}
                disabled={!oldPassword || newPassword.length < 6 || newPassword !== confirmPassword || isChangingPassword}
                className="px-4 py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
              >
                {isChangingPassword && <Loader2 className="animate-spin" size={16} />}
                {t('common.confirm')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reset Modal */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 max-w-md w-full border border-slate-200 dark:border-slate-700 shadow-2xl">
            <h3 className="text-xl font-bold text-red-600 dark:text-red-400 mb-2">{t('settings.general.dangerZone.modalTitle')}</h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 mb-4">
              {t('settings.general.dangerZone.modalWarning1')}
              <br />
              {t('settings.general.dangerZone.modalWarning2')}
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-300 mb-2">
              {t('settings.general.dangerZone.modalConfirmPrompt')}
            </p>
            <input
              type="text"
              value={resetInput}
              onChange={(e) => setResetInput(e.target.value)}
              className="w-full h-10 px-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-slate-100 outline-none focus:border-red-500 mb-6"
              placeholder="DELETE"
            />
            
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowResetModal(false);
                  setResetInput('');
                }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                disabled={isResetting}
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleFactoryReset}
                disabled={resetInput !== 'DELETE' || isResetting}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-red-500/50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
              >
                {isResetting && <Loader2 className="animate-spin" size={16} />}
                {t('common.confirm')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

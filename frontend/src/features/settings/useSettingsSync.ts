import { useEffect, useRef, useCallback } from 'react';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { useAuthStore } from '../../core/store/useAuthStore';

type SettingsSyncData = Partial<{
  openaiKey: string;
  geminiKey: string;
  ollamaBaseUrl: string;
  systemPrompt: string;
  theme: string;
  language: string;
}>;

const buildPayload = (data: SettingsSyncData): Record<string, string> => {
  const payload: Record<string, string> = {};
  if (data.openaiKey !== undefined) payload["llm.openai_key"] = data.openaiKey;
  if (data.geminiKey !== undefined) payload["llm.gemini_key"] = data.geminiKey;
  if (data.ollamaBaseUrl !== undefined) payload["llm.ollama_url"] = data.ollamaBaseUrl;
  if (data.systemPrompt !== undefined) payload["llm.system_prompt"] = data.systemPrompt;
  if (data.theme !== undefined) payload["general.theme"] = data.theme;
  if (data.language !== undefined) payload["general.language"] = data.language;
  return payload;
};

export const useSettingsSync = (data: SettingsSyncData| null, endpoint: string = 'http://localhost:8000/api/settings') => {
  const addToast = useSettingsStore(state => state.addToast);
  const token = useAuthStore(state => state.token);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isFirstRender = useRef(true);
  const prevData = useRef(data);
  const pendingPayload = useRef<Record<string, string> | null>(null);

  const doSave = useCallback(async (payload: Record<string, string>) => {
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(endpoint, {
        method: 'PUT',
        headers,
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        addToast('Settings saved');
      } else {
        console.error("Failed to save settings");
      }
    } catch (e) {
      console.error("Settings sync error", e);
    }
    pendingPayload.current = null;
  }, [token, endpoint, addToast]);

  useEffect(() => {

    if (data === null) return; // chưa load xong, bỏ qua hoàn toàn

    if (isFirstRender.current) {
      isFirstRender.current = false;
      prevData.current = data;
      return;
    }

    // Only sync if data actually changed
    if (JSON.stringify(prevData.current) === JSON.stringify(data)) {
      return;
    }
    
    prevData.current = data;
    const payload = buildPayload(data);
    pendingPayload.current = payload;

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      doSave(payload);
    }, 1000);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, doSave]);

  const doSaveRef = useRef(doSave);
  useEffect(() => {
    doSaveRef.current = doSave;
  }, [doSave]);

  // Flush pending save on unmount — prevents lost saves when modal closes
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (pendingPayload.current) {
        // Fire-and-forget the save before unmounting
        doSaveRef.current(pendingPayload.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
};

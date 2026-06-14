import { create } from 'zustand';
import { useChatStore } from './useChatStore';

interface AuthState {
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  const savedToken = localStorage.getItem('auth_token');
  return {
    token: savedToken,
    setToken: (token) => {
      if (token) {
        localStorage.setItem('auth_token', token);
      } else {
        localStorage.removeItem('auth_token');
      }
      set({ token });
    },
    logout: () => {
      localStorage.removeItem('auth_token');
      set({ token: null });
      useChatStore.getState().clearContext();
    }
  };
});

import { create } from 'zustand';

interface ToastMessage {
  id: string;
  message: string;
}

interface SettingsState {
  isSettingsOpen: boolean;
  isSidebarOpen: boolean;
  activeTab: 'general' | 'llm' | 'plugins';
  activeView: 'chat' | 'history' | 'notifications' | 'tasks' | 'calendar';
  isActivityDrawerOpen: boolean;
  activityDrawerWidth: number;
  toasts: ToastMessage[];
  isOnline: boolean;
  setSettingsOpen: (open: boolean) => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveTab: (tab: 'general' | 'llm' | 'plugins') => void;
  setActiveView: (view: 'chat' | 'history' | 'notifications' | 'tasks' | 'calendar') => void;
  setActivityDrawerOpen: (open: boolean) => void;
  setActivityDrawerWidth: (width: number) => void;
  setOnline: (online: boolean) => void;
  addToast: (message: string) => void;
  removeToast: (id: string) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  isSettingsOpen: false,
  isSidebarOpen: true,
  activeTab: 'general',
  activeView: 'chat',
  isActivityDrawerOpen: false,
  activityDrawerWidth: 350,
  toasts: [],
  isOnline: true,
  setSettingsOpen: (open) => set({ isSettingsOpen: open }),
  setSidebarOpen: (open) => set({ isSidebarOpen: open }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setActiveView: (view) => set({ activeView: view }),
  setActivityDrawerOpen: (open) => set({ isActivityDrawerOpen: open }),
  setActivityDrawerWidth: (width) => set({ activityDrawerWidth: width }),
  setOnline: (online) => set({ isOnline: online }),
  addToast: (message) => {
    const id = crypto.randomUUID();
    set((state) => ({ toasts: [...state.toasts, { id, message }] }));
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter(t => t.id !== id) }));
    }, 3000);
  },
  removeToast: (id) => set((state) => ({ toasts: state.toasts.filter(t => t.id !== id) })),
}));

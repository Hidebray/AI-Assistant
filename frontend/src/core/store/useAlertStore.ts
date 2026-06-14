import { create } from 'zustand';

type AlertUrgency = 'low' | 'high' | 'critical';

interface AlertData {
  id: string;
  urgency: AlertUrgency;
  title: string;
  message: string;
}

interface AlertState {
  currentAlert: AlertData | null;
  triggerAlert: (alert: Omit<AlertData, 'id'>) => void;
  clearAlert: () => void;
}

export const useAlertStore = create<AlertState>((set) => ({
  currentAlert: null,
  triggerAlert: (alertData) => {
    set({
      currentAlert: {
        ...alertData,
        id: Date.now().toString(),
      }
    });
  },
  clearAlert: () => set({ currentAlert: null }),
}));

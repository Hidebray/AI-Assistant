import { create } from 'zustand';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  isRead: boolean;
  isImportant: boolean;
  createdAt: string;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  setNotifications: (notifs: Notification[]) => void;
  addNotification: (notif: Notification) => void;
  markAllAsRead: () => void;
  deleteNotification: (id: string) => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
  setNotifications: (notifs) => set({ 
      notifications: notifs,
      unreadCount: notifs.filter(n => !n.isRead).length
  }),
  addNotification: (notif) => set((state) => {
      const newNotifs = [notif, ...state.notifications];
      return {
          notifications: newNotifs,
          unreadCount: newNotifs.filter(n => !n.isRead).length
      };
  }),
  markAllAsRead: () => set((state) => ({
      notifications: state.notifications.map(n => ({ ...n, isRead: true })),
      unreadCount: 0
  })),
  deleteNotification: (id) => set((state) => {
      const newNotifs = state.notifications.filter(n => n.id !== id);
      return {
          notifications: newNotifs,
          unreadCount: newNotifs.filter(n => !n.isRead).length
      };
  })
}));

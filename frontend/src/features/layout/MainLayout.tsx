import React, { useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { ChatArea } from '../chat/ChatArea';
import { HistoryView } from '../history/HistoryView';
import { NotificationHub } from '../notifications/NotificationHub';
import { TasksView } from '../tasks/TasksView';
import { CalendarView } from '../calendar/CalendarView';
import { SettingsModal } from '../settings/SettingsModal';
import { ToastContainer } from '../settings/ToastContainer';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { useNotificationStore } from '../../core/store/useNotificationStore';
import { useAuthStore } from '../../core/store/useAuthStore';
import { useChatStore } from '../../core/store/useChatStore';

export const MainLayout: React.FC = () => {
  const { activeView } = useSettingsStore();

  useEffect(() => {
    // Listen for spotlight commands
    let unlisten: (() => void) | undefined;
    try {
      import('@tauri-apps/api/event').then(({ listen }) => {
        listen<{ message: string }>('spotlight-command', (event) => {
          console.log('Received spotlight command:', event.payload.message);
          useChatStore.getState().setPendingSpotlightMessage(event.payload.message);
          useSettingsStore.getState().setActiveView('chat');
        }).then(unlistenFn => {
          unlisten = unlistenFn;
        });
      }).catch(() => {});
    } catch {
      // Ignore
    }

    // Xin quyền Native OS Notification khi khởi động MainLayout
    try {
      import('@tauri-apps/plugin-notification').then(async ({ isPermissionGranted, requestPermission }) => {
        const granted = await isPermissionGranted();
        if (!granted) {
          await requestPermission();
        }
      }).catch(() => {});
    } catch {
      // Ignore if not in Tauri
    }

    // Pre-fetch notifications for accurate badge count
    const fetchNotifications = async () => {
      const token = useAuthStore.getState().token;
      if (!token) return;
      try {
        const res = await fetch('http://localhost:8000/api/notifications', { 
          headers: { 'Authorization': `Bearer ${token}` } 
        });
        if (res.ok) {
          const data = await res.json();
          useNotificationStore.getState().setNotifications(data);
        }
      } catch (e) {
        console.error('Failed to pre-fetch notifications', e);
      }
    };
    fetchNotifications();

    return () => {
      if (unlisten) unlisten();
    };
  }, []);

  return (
    <div className="flex flex-row h-screen w-full bg-transparent overflow-hidden relative">
      <Sidebar />
      {activeView === 'chat' && <ChatArea />}
      {activeView === 'history' && <HistoryView />}
      {activeView === 'tasks' && <TasksView />}
      {activeView === 'calendar' && <CalendarView />}
      {activeView === 'notifications' && <NotificationHub />}
      <SettingsModal />
      <ToastContainer />
    </div>
  );
};

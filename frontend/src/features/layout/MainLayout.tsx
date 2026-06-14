import React, { useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { ChatArea } from '../chat/ChatArea';
import { HistoryView } from '../history/HistoryView';
import { NotificationHub } from '../notifications/NotificationHub';
import { SettingsModal } from '../settings/SettingsModal';
import { ToastContainer } from '../settings/ToastContainer';
import { useSettingsStore } from '../../core/store/useSettingsStore';

export const MainLayout: React.FC = () => {
  const { activeView } = useSettingsStore();

  useEffect(() => {
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
  }, []);

  return (
    <div className="flex flex-row h-screen w-full bg-transparent overflow-hidden relative">
      <Sidebar />
      {activeView === 'chat' && <ChatArea />}
      {activeView === 'history' && <HistoryView />}
      {activeView === 'notifications' && <NotificationHub />}
      <SettingsModal />
      <ToastContainer />
    </div>
  );
};

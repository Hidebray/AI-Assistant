import React from 'react';
import { Settings, MessageSquare, Clock, Bell, Menu, LogOut, ListTodo, Calendar as CalendarIcon } from 'lucide-react';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { useAuthStore } from '../../core/store/useAuthStore';
import { useTranslation } from 'react-i18next';
import { useNotificationStore } from '../../core/store/useNotificationStore';

export const Sidebar: React.FC = () => {
  const { t } = useTranslation();
  const { isSidebarOpen, setSidebarOpen, setSettingsOpen, activeView, setActiveView } = useSettingsStore();
  const { logout } = useAuthStore();
  const { unreadCount } = useNotificationStore();

  const navItems: Array<{ id: 'chat' | 'history' | 'tasks' | 'calendar' | 'notifications'; icon: any; label: string; badge?: number }> = [
    { id: 'chat', icon: MessageSquare, label: t('sidebar.chats') || 'Chat' },
    { id: 'history', icon: Clock, label: t('sidebar.history') || 'Lịch sử' },
    { id: 'tasks', icon: ListTodo, label: t('sidebar.tasks') || 'Công việc' },
    { id: 'calendar', icon: CalendarIcon, label: t('sidebar.calendar') || 'Lịch trình' },
    { id: 'notifications', icon: Bell, label: t('sidebar.notifications') || 'Thông báo', badge: unreadCount > 0 ? unreadCount : undefined }
  ];

  return (
    <div className={`h-full flex-shrink-0 bg-white/70 dark:bg-slate-900/60 backdrop-blur-3xl border-r border-slate-200 dark:border-white/10 flex flex-col z-20 transition-all duration-300 ${isSidebarOpen ? 'w-72' : 'w-[68px]'}`}>
      <div data-tauri-drag-region className={`h-14 border-b border-slate-200 dark:border-white/5 flex items-center shrink-0 transition-all duration-300 ${isSidebarOpen ? 'px-4 justify-between' : 'justify-center'}`}>
        <div className={`flex items-center text-slate-800 dark:text-white font-semibold cursor-default ${isSidebarOpen ? 'gap-2' : 'justify-center w-full'}`}>
          <Menu 
            size={18} 
            className="text-slate-500 dark:text-slate-400 cursor-pointer hover:text-slate-800 dark:hover:text-white transition-colors shrink-0" 
            onClick={() => setSidebarOpen(!isSidebarOpen)}
          />
          <span className={`transition-all duration-300 overflow-hidden whitespace-nowrap ${isSidebarOpen ? 'w-auto opacity-100' : 'w-0 opacity-0'}`}>
            AI Assistant
          </span>
        </div>
      </div>
      
      <div className={`flex-1 overflow-y-auto space-y-2 ${isSidebarOpen ? 'p-3' : 'p-2'}`}>
        {navItems.map(item => (
          <div 
            key={item.id}
            onClick={() => setActiveView(item.id)}
            title={!isSidebarOpen ? item.label : undefined}
            className={`rounded-lg text-sm cursor-pointer transition-all duration-300 flex items-center group relative ${isSidebarOpen ? 'p-3 justify-start' : 'p-3 justify-center'} ${activeView === item.id ? 'bg-primary-50 dark:bg-primary-500/20 text-primary-700 dark:text-white font-medium shadow-sm dark:shadow-none border border-primary-100 dark:border-transparent' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white border border-transparent'}`}
          >
            <div className={`flex items-center overflow-hidden ${isSidebarOpen ? 'gap-3 w-full' : 'justify-center w-full'}`}>
              <div className="relative">
                <item.icon size={20} className="shrink-0" />
                {item.badge && item.badge > 0 && !isSidebarOpen && (
                  <span className="absolute -top-1 -right-1 flex h-3 w-3 items-center justify-center rounded-full bg-red-500 text-[8px] font-bold text-white">
                    {item.badge}
                  </span>
                )}
              </div>
              <span className={`transition-all duration-300 overflow-hidden whitespace-nowrap ${isSidebarOpen ? 'w-full opacity-100' : 'w-0 opacity-0 hidden'}`}>
                {item.label}
              </span>
            </div>
            {item.badge && item.badge > 0 && isSidebarOpen && (
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white shrink-0 ml-2">
                {item.badge}
              </span>
            )}
          </div>
        ))}
      </div>

      <div className={`border-t border-slate-200 dark:border-white/5 space-y-3 transition-all duration-300 ${isSidebarOpen ? 'p-4' : 'p-2 py-4'}`}>
        <button 
          onClick={() => setSettingsOpen(true)}
          className={`w-full flex items-center text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-all duration-300 text-sm font-medium ${isSidebarOpen ? 'gap-3 justify-start' : 'justify-center'}`}
          title={!isSidebarOpen ? t('sidebar.settings') : undefined}
        >
          <Settings size={20} className="shrink-0" />
          <span className={`transition-all duration-300 overflow-hidden whitespace-nowrap ${isSidebarOpen ? 'w-auto opacity-100' : 'w-0 opacity-0 hidden'}`}>
            {t('sidebar.settings')}
          </span>
        </button>
        <button 
          onClick={() => logout()}
          className={`w-full flex items-center text-slate-600 dark:text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-all duration-300 text-sm font-medium ${isSidebarOpen ? 'gap-3 justify-start' : 'justify-center'}`}
          title={!isSidebarOpen ? t('sidebar.logout') : undefined}
        >
          <LogOut size={20} className="shrink-0" />
          <span className={`transition-all duration-300 overflow-hidden whitespace-nowrap ${isSidebarOpen ? 'w-auto opacity-100' : 'w-0 opacity-0 hidden'}`}>
            {t('sidebar.logout')}
          </span>
        </button>
      </div>
    </div>
  );
};

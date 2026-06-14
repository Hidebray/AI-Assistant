import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Bell, CheckCircle2, CalendarClock, AlertTriangle, Check, Trash2 } from 'lucide-react';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  isRead: boolean;
  createdAt: string;
  isImportant?: boolean;
}

// Mock data for now, since we haven't built a persistent notification DB yet
const mockNotifications: Notification[] = [
  {
    id: '1',
    title: 'Task sắp đến hạn',
    message: 'Công việc "Gửi báo cáo tài chính" sẽ đến hạn trong 30 phút nữa.',
    type: 'warning',
    isRead: false,
    createdAt: new Date().toISOString(),
    isImportant: true
  },
  {
    id: '2',
    title: 'Đồng bộ Email thành công',
    message: 'Đã tìm thấy 2 lịch hẹn mới từ Gmail và tự động thêm vào Calendar.',
    type: 'success',
    isRead: true,
    createdAt: new Date(Date.now() - 86400000).toISOString()
  }
];

export const NotificationHub: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'all' | 'unread' | 'important'>('all');
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);

  const filteredNotifs = notifications.filter(n => {
    if (activeTab === 'unread') return !n.isRead;
    if (activeTab === 'important') return n.isImportant;
    return true;
  });

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, isRead: true })));
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const getIcon = (type: string, isImportant?: boolean) => {
    if (isImportant) return <CalendarClock className="text-red-500" size={24} />;
    switch (type) {
      case 'success': return <CheckCircle2 className="text-emerald-500" size={24} />;
      case 'warning': return <AlertTriangle className="text-amber-500" size={24} />;
      case 'error': return <AlertTriangle className="text-red-500" size={24} />;
      default: return <Bell className="text-blue-500" size={24} />;
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 dark:bg-slate-900/50 p-8 overflow-y-auto">
      <div className="max-w-3xl mx-auto w-full">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-slate-800 dark:text-white">
              {t('sidebar.notifications') || 'Thông báo'}
            </h1>
            <span className="bg-red-500 text-white text-sm font-bold px-2.5 py-0.5 rounded-full">
              {notifications.filter(n => !n.isRead).length}
            </span>
          </div>
          
          <button 
            onClick={markAllAsRead}
            className="flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-500/10 px-4 py-2 rounded-lg transition-colors"
          >
            <Check size={16} />
            {t('notifications.markAllRead')}
          </button>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2 mb-6 border-b border-slate-200 dark:border-white/10 pb-4">
          <button 
            onClick={() => setActiveTab('all')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${activeTab === 'all' ? 'bg-slate-800 text-white dark:bg-white dark:text-slate-900' : 'text-slate-500 hover:bg-slate-200 dark:hover:bg-white/10'}`}
          >
            {t('notifications.all')}
          </button>
          <button 
            onClick={() => setActiveTab('unread')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${activeTab === 'unread' ? 'bg-slate-800 text-white dark:bg-white dark:text-slate-900' : 'text-slate-500 hover:bg-slate-200 dark:hover:bg-white/10'}`}
          >
            {t('notifications.unread')}
          </button>
          <button 
            onClick={() => setActiveTab('important')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${activeTab === 'important' ? 'bg-slate-800 text-white dark:bg-white dark:text-slate-900' : 'text-slate-500 hover:bg-slate-200 dark:hover:bg-white/10'}`}
          >
            {t('notifications.important')}
          </button>
        </div>

        {/* List */}
        <div className="space-y-3">
          {filteredNotifs.map(notif => {
            const date = new Date(notif.createdAt);
            const timeString = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            return (
              <div 
                key={notif.id} 
                className={`group flex items-start gap-4 p-4 rounded-2xl border transition-all duration-300 ${notif.isRead ? 'bg-white dark:bg-white/5 border-slate-200 dark:border-white/5 opacity-70' : 'bg-white dark:bg-white/10 border-primary-200 dark:border-primary-500/30 shadow-sm'}`}
              >
                <div className="mt-1 shrink-0 p-2 bg-slate-50 dark:bg-black/20 rounded-xl">
                  {getIcon(notif.type, notif.isImportant)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className={`font-semibold text-base ${notif.isRead ? 'text-slate-600 dark:text-slate-300' : 'text-slate-900 dark:text-white'}`}>
                          {notif.title}
                        </h4>
                        {!notif.isRead && (
                          <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0"></span>
                        )}
                        {notif.isImportant && (
                          <span className="bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                            {t('notifications.important')}
                          </span>
                        )}
                      </div>
                      <p className="text-slate-500 dark:text-slate-400 text-sm">
                        {notif.message}
                      </p>
                    </div>
                    <div className="text-xs font-medium text-slate-400 whitespace-nowrap shrink-0">
                      {timeString}
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => deleteNotification(notif.id)}
                  className="opacity-0 group-hover:opacity-100 p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-all"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            );
          })}
          
          {filteredNotifs.length === 0 && (
            <div className="text-center py-20 text-slate-500">
              <Bell size={48} className="mx-auto mb-4 opacity-20" />
              <p>{t('notifications.empty')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

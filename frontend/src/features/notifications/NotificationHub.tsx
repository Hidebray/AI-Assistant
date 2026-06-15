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

import { useNotificationStore } from '../../core/store/useNotificationStore';
import { useAuthStore } from '../../core/store/useAuthStore';

export const NotificationHub: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'all' | 'unread' | 'important'>('all');
  
  const { notifications, setNotifications, markAllAsRead, deleteNotification } = useNotificationStore();
  const { token } = useAuthStore();

  React.useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        const res = await fetch('http://localhost:8000/api/notifications', { headers });
        if (res.ok) {
          const data = await res.json();
          setNotifications(data);
        }
      } catch (e) {
        console.error('Failed to fetch notifications', e);
      }
    };
    fetchNotifications();
  }, [token, setNotifications]);

  const filteredNotifs = notifications.filter(n => {
    if (activeTab === 'unread') return !n.isRead;
    if (activeTab === 'important') return n.isImportant;
    return true;
  });

  const handleMarkAllAsRead = async () => {
    try {
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      await fetch('http://localhost:8000/api/notifications/read-all', { method: 'PUT', headers });
      markAllAsRead();
    } catch (e) {
      console.error('Failed to mark all as read', e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      await fetch(`http://localhost:8000/api/notifications/${id}`, { method: 'DELETE', headers });
      deleteNotification(id);
    } catch (e) {
      console.error('Failed to delete notification', e);
    }
  };

  const getIconConfig = (type: string, isImportant?: boolean) => {
    if (isImportant) return { icon: <CalendarClock className="text-red-600 dark:text-red-400" size={24} />, bg: "bg-red-50 dark:bg-red-500/10" };
    switch (type) {
      case 'success': return { icon: <CheckCircle2 className="text-emerald-600 dark:text-emerald-400" size={24} />, bg: "bg-emerald-50 dark:bg-emerald-500/10" };
      case 'warning': return { icon: <AlertTriangle className="text-amber-600 dark:text-amber-400" size={24} />, bg: "bg-amber-50 dark:bg-amber-500/10" };
      case 'error': return { icon: <AlertTriangle className="text-red-600 dark:text-red-400" size={24} />, bg: "bg-red-50 dark:bg-red-500/10" };
      default: return { icon: <Bell className="text-blue-600 dark:text-blue-400" size={24} />, bg: "bg-blue-50 dark:bg-blue-500/10" };
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
            <span className="bg-red-500 text-white text-sm font-bold px-2.5 py-0.5 rounded-full shadow-sm">
              {notifications.filter(n => !n.isRead).length}
            </span>
          </div>
          
          <button 
            onClick={handleMarkAllAsRead}
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
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${activeTab === 'all' ? 'bg-slate-800 text-white dark:bg-white dark:text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-slate-200 dark:hover:bg-white/10'}`}
          >
            {t('notifications.all')}
          </button>
          <button 
            onClick={() => setActiveTab('unread')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${activeTab === 'unread' ? 'bg-slate-800 text-white dark:bg-white dark:text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-slate-200 dark:hover:bg-white/10'}`}
          >
            {t('notifications.unread')}
          </button>
          <button 
            onClick={() => setActiveTab('important')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${activeTab === 'important' ? 'bg-slate-800 text-white dark:bg-white dark:text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-slate-200 dark:hover:bg-white/10'}`}
          >
            {t('notifications.important')}
          </button>
        </div>

        {/* List */}
        <div className="space-y-3">
          {filteredNotifs.map((notif, index) => {
            const date = new Date(notif.createdAt);
            const timeString = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const iconConfig = getIconConfig(notif.type, notif.isImportant);
            
            return (
              <div 
                key={notif.id} 
                style={{ animationDelay: `${index * 50}ms` }}
                className={`group flex items-start gap-4 p-4 rounded-2xl border transition-all duration-300 opacity-0 animate-fade-in-up ${notif.isRead ? 'bg-white dark:bg-white/5 border-slate-200 dark:border-white/5 opacity-70' : 'bg-white dark:bg-white/10 border-primary-200 dark:border-primary-500/30 shadow-sm hover:shadow-[0_8px_30px_rgba(99,102,241,0.15)] dark:hover:shadow-[0_8px_30px_rgba(99,102,241,0.2)] dark:hover:border-primary-400'}`}
              >
                <div className={`mt-1 shrink-0 p-3 rounded-xl shadow-sm ${iconConfig.bg} group-hover:scale-105 transition-transform`}>
                  {iconConfig.icon}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className={`font-semibold text-base ${notif.isRead ? 'text-slate-600 dark:text-slate-300' : 'text-slate-900 dark:text-white'}`}>
                          {notif.title}
                        </h4>
                        {!notif.isRead && (
                          <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0 shadow-[0_0_8px_rgba(59,130,246,0.6)]"></span>
                        )}
                        {notif.isImportant && (
                          <span className="bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                            {t('notifications.important')}
                          </span>
                        )}
                      </div>
                      <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">
                        {notif.message}
                      </p>
                    </div>
                    <div className="text-xs font-medium text-slate-400 whitespace-nowrap shrink-0 mt-1">
                      {timeString}
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => handleDelete(notif.id)}
                  className="opacity-0 group-hover:opacity-100 p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-all"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            );
          })}
          
          {/* Empty State */}
          {filteredNotifs.length === 0 && (
            <div className="flex flex-col items-center justify-center text-slate-400 dark:text-slate-500 mt-24 opacity-0 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
              <div className="w-24 h-24 mb-6 rounded-full bg-slate-100 dark:bg-slate-800/50 flex items-center justify-center">
                <Bell size={40} className="opacity-50" />
              </div>
              <p className="text-lg font-medium">{t('notifications.empty') || 'Không có thông báo nào ở đây.'}</p>
              <p className="text-sm mt-2 opacity-70">Bạn đã cập nhật tất cả thông tin mới nhất.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

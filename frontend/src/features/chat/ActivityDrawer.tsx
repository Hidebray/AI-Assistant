import React, { useState, useEffect } from 'react';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { Zap, Activity, Mail, Calendar as CalendarIcon, CheckCircle2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface ActivityLog {
  id: string;
  type: string;
  message: string;
  timestamp: string;
}

export const ActivityDrawer: React.FC = () => {
  const { t } = useTranslation();
  const { isActivityDrawerOpen, activityDrawerWidth, setActivityDrawerWidth } = useSettingsStore();
  
  const [isResizing, setIsResizing] = useState(false);
  const [logs, setLogs] = useState<ActivityLog[]>([
    { id: '1', type: 'system', message: 'AgentCore initialized.', timestamp: new Date().toISOString() },
    { id: '2', type: 'plugin_email', message: 'EmailScannerWorker is running.', timestamp: new Date().toISOString() }
  ]);

  const MIN_WIDTH = 300;
  const MAX_WIDTH = 500;

  // Setup WebSocket or EventBus listener here for real logs
  useEffect(() => {
    const handleEventBus = (e: any) => {
      const event = e.detail;
      setLogs(prev => {
        const newLogs = [...prev, {
          id: crypto.randomUUID(),
          type: event.type || 'system',
          message: event.message || JSON.stringify(event),
          timestamp: new Date().toISOString()
        }];
        return newLogs.slice(-50); // Keep last 50 logs
      });
    };
    window.addEventListener('event-bus-log', handleEventBus);
    return () => window.removeEventListener('event-bus-log', handleEventBus);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      // Calculate new width: window.innerWidth - mouse X position
      // This is because the drawer is on the right
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
        setActivityDrawerWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      // Disable text selection while resizing
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
    };
  }, [isResizing, setActivityDrawerWidth]);

  const getIcon = (type: string) => {
    if (type.includes('email')) return <Mail size={16} className="text-blue-500" />;
    if (type.includes('calendar')) return <CalendarIcon size={16} className="text-purple-500" />;
    if (type.includes('success')) return <CheckCircle2 size={16} className="text-emerald-500" />;
    return <Zap size={16} className="text-amber-500" />;
  };

  return (
    <div 
      className={`h-full bg-white dark:bg-slate-900/80 backdrop-blur-md border-l border-slate-200 dark:border-white/10 flex flex-col transition-transform duration-300 relative z-20 shrink-0 ${isActivityDrawerOpen ? 'translate-x-0' : 'translate-x-full absolute right-0'}`}
      style={{ width: isActivityDrawerOpen ? `${activityDrawerWidth}px` : '0px' }}
    >
      {/* Resizer Handle */}
      {isActivityDrawerOpen && (
        <div 
          className="absolute left-0 top-0 bottom-0 w-1.5 cursor-col-resize hover:bg-primary-500/50 active:bg-primary-500 transition-colors z-30"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizing(true);
          }}
        />
      )}

      <div className="h-14 border-b border-slate-200 dark:border-white/5 flex items-center px-4 shrink-0">
        <Activity size={18} className="text-slate-500 mr-2" />
        <span className="font-semibold text-slate-800 dark:text-white">{t('chat.activity')}</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-white/10">
        {logs.map(log => {
          const date = new Date(log.timestamp);
          const timeString = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          return (
            <div key={log.id} className="flex gap-3 text-sm">
              <div className="mt-0.5 shrink-0">
                {getIcon(log.type)}
              </div>
              <div>
                <span className="text-xs text-slate-400 font-mono mb-1 block">{timeString}</span>
                <p className="text-slate-600 dark:text-slate-300 break-words leading-relaxed">{log.message}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

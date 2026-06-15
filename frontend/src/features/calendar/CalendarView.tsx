import React, { useEffect } from 'react';
import { useCalendarStore } from '../../core/store/useCalendarStore';
import { useTranslation } from 'react-i18next';
import { Calendar as CalendarIcon, Clock, MapPin, Plus, Trash2 } from 'lucide-react';

export const CalendarView: React.FC = () => {
  const { t } = useTranslation();
  const { events, isLoading, fetchEvents, deleteEvent } = useCalendarStore();

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return (
    <div className="flex-1 h-full bg-slate-50 dark:bg-slate-900 flex flex-col relative overflow-hidden">
      <header data-tauri-drag-region className="h-14 flex items-center justify-between px-6 border-b border-slate-200 dark:border-white/10 shrink-0 bg-white dark:bg-slate-900">
        <h1 className="text-lg font-semibold text-slate-800 dark:text-white">
          {t('sidebar.calendar') || 'Lịch trình'}
        </h1>
        <button className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg transition-colors">
          <Plus size={16} />
          <span>Tạo sự kiện</span>
        </button>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        {isLoading && events.length === 0 ? (
          <div className="flex justify-center items-center h-full text-slate-500">Đang tải...</div>
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <CalendarIcon size={48} className="text-slate-300 dark:text-slate-700 mb-4" />
            <p>Không có sự kiện nào sắp tới.</p>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {events.map(event => (
              <div key={event.id} className="group bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-200 dark:border-white/10 shadow-sm hover:shadow-md transition-all flex flex-col">
                <div className="flex justify-between items-start mb-3">
                  <div className="bg-primary-100 dark:bg-primary-500/20 text-primary-700 dark:text-primary-400 p-2 rounded-xl">
                    <CalendarIcon size={20} />
                  </div>
                  <button 
                    onClick={() => deleteEvent(event.id)}
                    className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-white mb-2 line-clamp-2">
                  {event.title}
                </h3>
                <div className="mt-auto space-y-2 text-sm text-slate-600 dark:text-slate-400">
                  <div className="flex items-center gap-2">
                    <Clock size={16} className="shrink-0" />
                    <span className="truncate">
                      {new Date(event.start_time).toLocaleString()}
                    </span>
                  </div>
                  {event.location && (
                    <div className="flex items-center gap-2">
                      <MapPin size={16} className="shrink-0" />
                      <span className="truncate">{event.location}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

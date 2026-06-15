import React, { useEffect } from 'react';
import { useTaskStore } from '../../core/store/useTaskStore';
import { useTranslation } from 'react-i18next';
import { CheckCircle2, Circle, Clock, Plus, Trash2 } from 'lucide-react';

export const TasksView: React.FC = () => {
  const { t } = useTranslation();
  const { tasks, isLoading, fetchTasks, updateTaskStatus, deleteTask } = useTaskStore();

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  return (
    <div className="flex-1 h-full bg-white dark:bg-slate-900 flex flex-col relative overflow-hidden">
      <header data-tauri-drag-region className="h-14 flex items-center justify-between px-6 border-b border-slate-200 dark:border-white/10 shrink-0">
        <h1 className="text-lg font-semibold text-slate-800 dark:text-white">
          {t('sidebar.tasks') || 'Công việc'}
        </h1>
        <button className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg transition-colors">
          <Plus size={16} />
          <span>Tạo mới</span>
        </button>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        {isLoading && tasks.length === 0 ? (
          <div className="flex justify-center items-center h-full text-slate-500">Đang tải...</div>
        ) : tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <CheckCircle2 size={48} className="text-slate-300 dark:text-slate-700 mb-4" />
            <p>Không có công việc nào.</p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {tasks.map(task => (
              <div key={task.id} className={`flex items-start gap-4 p-4 rounded-xl border transition-all ${task.status === 'completed' ? 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-white/5 opacity-70' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-white/10 shadow-sm hover:shadow-md'}`}>
                <button 
                  onClick={() => updateTaskStatus(task.id, task.status === 'completed' ? 'pending' : 'completed')}
                  className="mt-1 shrink-0 text-slate-400 hover:text-primary-500 transition-colors"
                >
                  {task.status === 'completed' ? (
                    <CheckCircle2 size={24} className="text-emerald-500" />
                  ) : (
                    <Circle size={24} />
                  )}
                </button>
                <div className="flex-1 min-w-0">
                  <h3 className={`text-base font-medium ${task.status === 'completed' ? 'text-slate-500 line-through' : 'text-slate-800 dark:text-white'}`}>
                    {task.title}
                  </h3>
                  {task.description && (
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                      {task.description}
                    </p>
                  )}
                  <div className="flex items-center gap-4 mt-3 text-xs font-medium">
                    {task.deadline && (
                      <span className={`flex items-center gap-1 ${new Date(task.deadline) < new Date() && task.status !== 'completed' ? 'text-red-500' : 'text-slate-500'}`}>
                        <Clock size={14} />
                        {new Date(task.deadline).toLocaleString()}
                      </span>
                    )}
                    <span className={`px-2 py-0.5 rounded-full capitalize ${task.priority === 'high' ? 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400' : task.priority === 'medium' ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400' : 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400'}`}>
                      {task.priority}
                    </span>
                  </div>
                </div>
                <button 
                  onClick={() => deleteTask(task.id)}
                  className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

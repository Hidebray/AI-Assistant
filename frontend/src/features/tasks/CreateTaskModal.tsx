import React, { useState } from 'react';
import { useTaskStore } from '../../core/store/useTaskStore';
import { X } from 'lucide-react';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateTaskModal: React.FC<CreateTaskModalProps> = ({ isOpen, onClose }) => {
  const createTask = useTaskStore(state => state.createTask);
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [deadline, setDeadline] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    
    setIsSubmitting(true);
    try {
      // If deadline is provided, make sure it's ISO
      const deadlineValue = deadline ? new Date(deadline).toISOString() : undefined;
      
      await createTask({
        title: title.trim(),
        description: description.trim() || undefined,
        deadline: deadlineValue,
        priority
      });
      
      // Reset and close
      setTitle('');
      setDescription('');
      setDeadline('');
      setPriority('medium');
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div 
        className="bg-white dark:bg-slate-900 w-full max-w-md rounded-2xl shadow-xl border border-slate-200 dark:border-white/10 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        role="dialog"
      >
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-100 dark:border-white/5">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-white">Tạo công việc mới</h2>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/10 p-1.5 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Tên công việc <span className="text-red-500">*</span></label>
            <input 
              type="text" 
              value={title}
              onChange={e => setTitle(e.target.value)}
              required
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="VD: Mua sắm cuối tuần"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Mô tả chi tiết</label>
            <textarea 
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 min-h-[80px]"
              placeholder="Ghi chú thêm..."
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Hạn chót (Deadline)</label>
              <input 
                type="datetime-local" 
                value={deadline}
                onChange={e => setDeadline(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 [color-scheme:light] dark:[color-scheme:dark]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Mức độ ưu tiên</label>
              <select 
                value={priority}
                onChange={e => setPriority(e.target.value as any)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="low">Thấp (Low)</option>
                <option value="medium">Trung bình (Medium)</option>
                <option value="high">Cao (High)</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-100 dark:border-white/5">
            <button 
              type="button" 
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg transition-colors"
            >
              Hủy
            </button>
            <button 
              type="submit" 
              disabled={!title.trim() || isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:hover:bg-primary-600 rounded-lg transition-colors"
            >
              {isSubmitting ? 'Đang lưu...' : 'Lưu công việc'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

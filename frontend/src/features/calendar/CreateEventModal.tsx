import React, { useState } from 'react';
import { useCalendarStore } from '../../core/store/useCalendarStore';
import { X } from 'lucide-react';

interface CreateEventModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateEventModal: React.FC<CreateEventModalProps> = ({ isOpen, onClose }) => {
  const createEvent = useCalendarStore(state => state.createEvent);
  
  const [title, setTitle] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [location, setLocation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !startTime || !endTime) return;
    
    setIsSubmitting(true);
    try {
      await createEvent({
        title: title.trim(),
        start_time: new Date(startTime).toISOString(),
        end_time: new Date(endTime).toISOString(),
        location: location.trim() || undefined
      });
      
      // Reset and close
      setTitle('');
      setStartTime('');
      setEndTime('');
      setLocation('');
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
          <h2 className="text-lg font-semibold text-slate-800 dark:text-white">Tạo sự kiện mới</h2>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/10 p-1.5 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Tên sự kiện <span className="text-red-500">*</span></label>
            <input 
              type="text" 
              value={title}
              onChange={e => setTitle(e.target.value)}
              required
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="VD: Họp với khách hàng"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Bắt đầu <span className="text-red-500">*</span></label>
              <input 
                type="datetime-local" 
                value={startTime}
                onChange={e => setStartTime(e.target.value)}
                required
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 [color-scheme:light] dark:[color-scheme:dark]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Kết thúc <span className="text-red-500">*</span></label>
              <input 
                type="datetime-local" 
                value={endTime}
                onChange={e => setEndTime(e.target.value)}
                required
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 [color-scheme:light] dark:[color-scheme:dark]"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Địa điểm</label>
            <input 
              type="text" 
              value={location}
              onChange={e => setLocation(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="VD: Phòng họp A"
            />
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
              disabled={!title.trim() || !startTime || !endTime || isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:hover:bg-primary-600 rounded-lg transition-colors"
            >
              {isSubmitting ? 'Đang lưu...' : 'Lưu sự kiện'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

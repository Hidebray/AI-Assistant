import React from 'react';
import { WifiOff } from 'lucide-react';
import { useSettingsStore } from '../../core/store/useSettingsStore';

export const OfflineBanner: React.FC = () => {
  const isOnline = useSettingsStore(state => state.isOnline);

  if (isOnline) return null;

  return (
    <div className="w-full bg-amber-500/10 border-b border-amber-500/20 py-2 px-4 flex items-center justify-center gap-2 animate-in slide-in-from-top-full duration-300 shrink-0">
      <WifiOff size={16} className="text-amber-500" />
      <span className="text-sm font-medium text-amber-500">
        Bạn đang ngoại tuyến. Nhập '/' để dùng lệnh cục bộ (VD: /calendar, /note, /task).
      </span>
    </div>
  );
};

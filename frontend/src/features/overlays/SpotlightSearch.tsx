import React, { useEffect, useRef, useState } from 'react';
import { Search } from 'lucide-react';
import { register, unregister } from '@tauri-apps/plugin-global-shortcut';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';
import { emit } from '@tauri-apps/api/event';

export const SpotlightSearch: React.FC = () => {
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState('');

  useEffect(() => {
    let isRegistered = false;
    const setupShortcut = async () => {
      try {
        await register('Alt+Space', async (event) => {
          if (event.state === 'Pressed') {
            const appWindow = getCurrentWebviewWindow();
            const isVisible = await appWindow.isVisible();
            if (isVisible) {
              await appWindow.hide();
            } else {
              await appWindow.show();
              await appWindow.setFocus();
              inputRef.current?.focus();
            }
          }
        });
        isRegistered = true;
      } catch (err) {
        console.error('Lỗi đăng ký phím tắt:', err);
      }
    };
    
    // Auto focus when component mounts
    const timer = setTimeout(() => {
      inputRef.current?.focus();
    }, 100);

    // Call setup if not already registered (usually only runs once)
    setupShortcut();

    return () => {
      clearTimeout(timer);
      if (isRegistered) {
        unregister('Alt+Space').catch(console.error);
      }
    };
  }, []);

  const handleKeyDown = async (e: React.KeyboardEvent) => {
    const appWindow = getCurrentWebviewWindow();
    if (e.key === 'Enter' && query.trim()) {
      // Send command via Tauri event to the main window
      console.log('Sending command via event:', query);
      await emit('spotlight-command', { message: query.trim() });
      setQuery('');
      await appWindow.hide();
    } else if (e.key === 'Escape') {
      await appWindow.hide();
    }
  };

  return (
    <div ref={containerRef} className="w-full h-screen flex items-center justify-center p-4 bg-transparent overflow-hidden">
      <div className="w-full max-w-2xl bg-slate-900/60 backdrop-blur-3xl shadow-2xl rounded-2xl flex items-center px-6 py-4 border border-white/20">
        <Search size={32} className="text-slate-400 mr-4 shrink-0" />
        <input 
          ref={inputRef}
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Nhập lệnh hoặc hỏi AI..." 
          className="flex-1 bg-transparent border-none outline-none text-2xl text-white placeholder-slate-500"
        />
      </div>
    </div>
  );
};

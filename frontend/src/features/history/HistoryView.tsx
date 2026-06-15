import React, { useEffect } from 'react';
import { useChatStore } from '../../core/store/useChatStore';
import { useAuthStore } from '../../core/store/useAuthStore';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { MessageSquare, Clock, Search, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const HistoryView: React.FC = () => {
  const { t } = useTranslation();
  const { conversations, setConversations, setActiveConversation, setMessages } = useChatStore();
  const { token } = useAuthStore();
  const { setActiveView } = useSettingsStore();
  const [searchTerm, setSearchTerm] = React.useState('');

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        const res = await fetch('http://localhost:8000/api/conversations', { headers });
        if (res.ok) {
          const data = await res.json();
          setConversations(data);
        }
      } catch (e) {
        console.error('Failed to fetch conversations', e);
      }
    };
    fetchConversations();
  }, [token, setConversations]);

  const deleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      
      const res = await fetch(`http://localhost:8000/api/conversations/${id}`, { method: 'DELETE', headers });
      if (res.ok) {
        setConversations(conversations.filter(c => c.id !== id));
      }
    } catch (e) {
      console.error('Failed to delete conversation', e);
    }
  };

  const openConversation = (id: string) => {
    setMessages([]);
    setActiveConversation(id);
    setActiveView('chat');
  };

  const filteredConvs = conversations.filter(c => 
    c.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 dark:bg-slate-900/50 p-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto w-full">
        {/* Header and Search */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-800 dark:text-white mb-6">
            {t('sidebar.history') || 'Lịch sử trò chuyện'}
          </h1>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder={t('history.search') || 'Tìm kiếm...'} 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-3 rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-black/20 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 w-full shadow-sm transition-all"
            />
          </div>
        </div>

        {/* List View */}
        <div className="flex flex-col gap-4">
          {filteredConvs.map((conv, index) => {
            const date = new Date(conv.updated_at);
            const isToday = date.toDateString() === new Date().toDateString();
            const formattedDate = (isToday ? 'Hôm nay' : date.toLocaleDateString()) + ', ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            return (
              <div 
                key={conv.id}
                onClick={() => openConversation(conv.id)}
                style={{ animationDelay: `${index * 50}ms` }}
                className="group relative flex items-start gap-5 bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-2xl p-5 cursor-pointer hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:border-primary-300 dark:hover:shadow-[0_8px_30px_rgba(99,102,241,0.1)] dark:hover:border-primary-500/50 transition-all duration-300 opacity-0 animate-fade-in-up"
              >
                {/* Icon Left */}
                <div className="p-3 bg-primary-600 dark:bg-primary-500 rounded-xl text-white shadow-sm shrink-0 mt-0.5 group-hover:scale-105 transition-transform">
                  <MessageSquare size={24} />
                </div>
                
                {/* Content Right */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4 mb-1">
                    <h3 className="font-semibold text-slate-800 dark:text-white text-lg truncate">
                      {conv.title}
                    </h3>
                    <button 
                      onClick={(e) => deleteConversation(conv.id, e)}
                      className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-md opacity-0 group-hover:opacity-100 transition-all shrink-0"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                  
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-3 line-clamp-1">
                    {conv.summary_content || "Bắt đầu cuộc trò chuyện mới..."}
                  </p>
                  
                  <div className="flex items-center gap-5 text-xs font-medium text-slate-500 dark:text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <Clock size={14} />
                      <span>{formattedDate}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <MessageSquare size={14} />
                      <span>{conv.message_count || 0} tin nhắn</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Empty State */}
        {filteredConvs.length === 0 && (
          <div className="flex flex-col items-center justify-center text-slate-400 dark:text-slate-500 mt-24 opacity-0 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
            <div className="w-24 h-24 mb-6 rounded-full bg-slate-100 dark:bg-slate-800/50 flex items-center justify-center">
              <MessageSquare size={40} className="opacity-50" />
            </div>
            <p className="text-lg font-medium">{t('history.noConversations') || 'Chưa có cuộc trò chuyện nào'}</p>
            <p className="text-sm mt-2 opacity-70">Hãy bắt đầu một cuộc trò chuyện mới để lưu lại tại đây.</p>
          </div>
        )}
      </div>
    </div>
  );
};

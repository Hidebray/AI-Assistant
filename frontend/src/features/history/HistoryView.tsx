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
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-slate-800 dark:text-white">
            {t('sidebar.history') || 'Lịch sử trò chuyện'}
          </h1>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder={t('history.search')} 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-black/20 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 w-64"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredConvs.map(conv => {
            const date = new Date(conv.updated_at);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            return (
              <div 
                key={conv.id}
                onClick={() => openConversation(conv.id)}
                className="group relative bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-2xl p-5 cursor-pointer hover:shadow-lg hover:border-primary-200 dark:hover:border-primary-500/30 transition-all duration-300"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2 bg-primary-50 dark:bg-primary-500/20 rounded-lg text-primary-600 dark:text-primary-400">
                    <MessageSquare size={20} />
                  </div>
                  <button 
                    onClick={(e) => deleteConversation(conv.id, e)}
                    className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-md opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                
                <h3 className="font-semibold text-slate-800 dark:text-white text-lg mb-2 line-clamp-2">
                  {conv.title}
                </h3>
                
                <div className="flex items-center gap-4 text-xs font-medium text-slate-500 dark:text-slate-400 mt-4">
                  <div className="flex items-center gap-1.5">
                    <Clock size={14} />
                    <span>{formattedDate}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <MessageSquare size={14} />
                    <span>{conv.message_count || 0} {t('history.messages')}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {filteredConvs.length === 0 && (
          <div className="text-center text-slate-500 dark:text-slate-400 mt-20">
            {t('history.noConversations')}
          </div>
        )}
      </div>
    </div>
  );
};

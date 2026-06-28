import React, { useRef, useEffect, useState } from 'react';

import { useChatStore } from '../../core/store/useChatStore';
import { useAuthStore } from '../../core/store/useAuthStore';
import { MessageBubble } from './MessageBubble';
import { AgentStatusIndicator } from './AgentStatusIndicator';
import { ChatInput } from './ChatInput';
import { useTranslation } from 'react-i18next';

import { ActivityDrawer } from './ActivityDrawer';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { Activity, Sparkles, SquarePen } from 'lucide-react';

interface BackendMessage {
  id: string;
  sender_role: 'user' | 'assistant' | 'system';
  content: string;
  plan?: unknown;
}

export const ChatArea: React.FC = () => {
  const { t } = useTranslation();
  const { messages, setMessages, activeConversationId, setActiveConversation, streamingContent, isStreaming, pendingSpotlightMessage, setPendingSpotlightMessage, sendMessage, stopGenerating } = useChatStore();
  const token = useAuthStore(state => state.token);
  const { isActivityDrawerOpen, setActivityDrawerOpen } = useSettingsStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
  }, [messages, streamingContent]);

  useEffect(() => {
    const handleSend = (e: any) => sendMessage(e.detail);
    window.addEventListener('send-chat-message', handleSend);
    return () => window.removeEventListener('send-chat-message', handleSend);
  }, [sendMessage]);

  useEffect(() => {
    if (pendingSpotlightMessage) {
      setPendingSpotlightMessage(null);
      // Timeout is needed if the connection was just initiated or component just mounted
      setTimeout(() => {
        sendMessage(pendingSpotlightMessage);
      }, 100);
    }
  }, [pendingSpotlightMessage, sendMessage, setPendingSpotlightMessage]);

  useEffect(() => {
    const abortController = new AbortController();
    const targetId = activeConversationId;

    const loadHistory = async () => {
      if (!targetId) return;
      setIsLoading(true);
      try {
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const res = await fetch(`http://localhost:8000/api/conversations/${targetId}/messages`, {
          headers,
          signal: abortController.signal
        });

        // If this request was aborted (user switched conversation), don't update state
        if (abortController.signal.aborted) return;

        if (res.ok) {
          const data = await res.json();

          // Double-check: is this still the active conversation?
          const currentActiveId = useChatStore.getState().activeConversationId;
          if (currentActiveId !== targetId) return;

          // Guard for lazy creation: if backend has 0 messages but we already have
          // a local user message (just sent), don't wipe it. But if we also have 0
          // local messages, this is just an empty conversation — allow it through.
          const currentMessages = useChatStore.getState().messages;
          if (data.length === 0 && currentMessages.length > 0) {
            return;
          }

          // Map backend messages to frontend format
          const mapped = (data as BackendMessage[]).map((m) => ({
            id: m.id,
            role: m.sender_role,
            content: m.content,
            plan: m.plan as never
          }));
          setMessages(mapped);
        }
      } catch (e: unknown) {
        if (e instanceof DOMException && e.name === 'AbortError') return;
        console.error("Failed to load chat history", e);
      } finally {
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
      }
    };
    loadHistory();

    return () => {
      abortController.abort();
    };
  }, [activeConversationId, token, setMessages]);

  const isNewChat = messages.length === 0 && !isStreaming && !isLoading;

  const handleNewChat = () => {
    setActiveConversation(null as unknown as string);
    setMessages([]);
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      <div className="flex-1 flex flex-col relative h-full min-w-0">
        <header data-tauri-drag-region className="h-14 flex items-center justify-between px-6 border-b border-slate-200 dark:border-white/10 bg-white/50 dark:bg-black/10 backdrop-blur-md shrink-0 select-none z-10 transition-colors">
          <AgentStatusIndicator />
          <div className="flex items-center gap-2">
            <button 
              onClick={handleNewChat}
              className="p-2 rounded-lg transition-colors text-slate-500 hover:bg-slate-100 dark:hover:bg-white/10"
              title={t('chat.newChat') || 'Trò chuyện mới'}
            >
              <SquarePen size={18} />
            </button>
            <button 
              onClick={() => setActivityDrawerOpen(!isActivityDrawerOpen)}
              className={`p-2 rounded-lg transition-colors relative ${isActivityDrawerOpen ? 'bg-primary-100 text-primary-600 dark:bg-primary-500/20 dark:text-primary-400' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-white/10'}`}
              title="Hoạt động"
            >
              <Activity size={18} />
              {/* Thêm indicator dot (ví dụ đỏ/xanh) toả sáng */}
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse"></span>
            </button>
          </div>
        </header>


      <div className={`flex-1 overflow-y-auto overflow-x-hidden p-6 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-white/10 scrollbar-track-transparent ${isNewChat ? 'flex flex-col' : ''}`}>
        <div className={`max-w-4xl mx-auto w-full flex flex-col ${isNewChat ? 'flex-1 justify-center' : ''}`}>
          
          {isLoading && (
            <div className="flex justify-center mt-10">
              <span className="text-slate-500 dark:text-slate-400 animate-pulse">{t('chat.loadingHistory')}</span>
            </div>
          )}

          {!isNewChat && messages.map((msg) => (
            <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
          ))}

          {!isNewChat && isStreaming && (
             <MessageBubble role="assistant" content={streamingContent} />
          )}

          {isNewChat ? (
            <div className="flex flex-col items-center justify-center w-full transform -translate-y-10">
              <div className="relative mb-6 group cursor-pointer">
                {/* Glow Backdrop */}
                <div className="absolute inset-[-20%] bg-gradient-to-tr from-transparent via-primary-500/30 to-transparent blur-2xl rounded-full animate-pulse group-hover:via-primary-500/50 transition-colors duration-500"></div>
                
                {/* Badge Container */}
                <div className="w-24 h-24 rounded-full bg-slate-900/40 dark:bg-black/40 border border-slate-200/50 dark:border-white/10 flex items-center justify-center shadow-lg backdrop-blur-xl relative z-10 overflow-hidden group-hover:scale-105 transition-transform duration-500">
                  {/* Rotating Inner Glow */}
                  <div className="absolute inset-[-150%] bg-gradient-to-tr from-transparent via-primary-glow to-transparent opacity-20 group-hover:opacity-40 transition-opacity duration-500 animate-[spin_4s_linear_infinite]"></div>
                  
                  {/* Core Inner Circle */}
                  <div className="absolute inset-[3px] rounded-full bg-white dark:bg-slate-900 flex items-center justify-center z-10">
                    <Sparkles size={40} className="text-primary-500 drop-shadow-md" />
                  </div>
                </div>
              </div>
              <p className="text-2xl font-semibold text-slate-800 dark:text-slate-200 mb-8 tracking-tight">{t('chat.greeting')}</p>
              <div className="w-full">
                <ChatInput sendMessage={sendMessage} stopGenerating={stopGenerating} isNewChat={true} />
              </div>
            </div>
          ) : (
            <div ref={messagesEndRef} className="h-4" />
          )}
        </div>
      </div>

        {!isNewChat && <ChatInput sendMessage={sendMessage} stopGenerating={stopGenerating} isNewChat={false} />}
      </div>
      
      {/* Drawer */}
      <ActivityDrawer />
    </div>
  );
};

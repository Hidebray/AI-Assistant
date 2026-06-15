import { useEffect, useRef, useCallback } from 'react';
import { useChatStore } from '../../core/store/useChatStore';
import { useAuthStore } from '../../core/store/useAuthStore';
import { useSettingsStore } from '../../core/store/useSettingsStore';
import { useAlertStore } from '../../core/store/useAlertStore';

export const useChatWebSocket = () => {
  const ws = useRef<WebSocket | null>(null);
  const clientId = useRef<string | null>(null);
  const reconnectTimer = useRef<number | null>(null);
  const connectRef = useRef<(() => void) | null>(null);

  const scheduleReconnect = useCallback(() => {
    reconnectTimer.current = window.setTimeout(() => {
      connectRef.current?.();
    }, 3000);
  }, []);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    if (!clientId.current) {
      clientId.current = `client-${crypto.randomUUID()}`;
    }

    ws.current = new WebSocket(`ws://localhost:8000/ws/chat/${clientId.current}`);

    ws.current.onopen = () => {
      // Send authenticate payload
      const token = useAuthStore.getState().token || "dummy_token";
      ws.current?.send(JSON.stringify({
        type: "AUTHENTICATE",
        token: token
      }));
    };

    ws.current.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        const { appendStreamChunk, commitStream } = useChatStore.getState();

        if (data.type === "chunk") {
          appendStreamChunk(data.content);
        } else if (data.type === "status") {
          console.log("Agent Status:", data.content);
          window.dispatchEvent(new CustomEvent('event-bus-log', {
            detail: {
              type: 'system',
              message: data.content
            }
          }));
        } else if (data.type === "alert") {
          console.log("System Alert:", data.message);
          
          const urgencyUpper = data.urgency.toUpperCase();
          const title = urgencyUpper === 'CRITICAL' ? 'Cảnh báo khẩn cấp' : 'Thông báo hệ thống';
          
          useAlertStore.getState().triggerAlert({
            urgency: data.urgency,
            title: title,
            message: data.message
          });

          // Add to NotificationStore for persistent UI
          const { useNotificationStore } = await import('../../core/store/useNotificationStore');
          useNotificationStore.getState().addNotification({
            id: crypto.randomUUID(), // Will be overwritten by DB on refresh, but good for local state
            title: title,
            message: data.message,
            type: urgencyUpper === 'CRITICAL' ? 'error' : (urgencyUpper === 'HIGH' ? 'warning' : 'info'),
            isRead: false,
            isImportant: urgencyUpper === 'CRITICAL' || urgencyUpper === 'HIGH',
            createdAt: new Date().toISOString()
          });
          // Try to use Tauri notification if available
          try {
            import('@tauri-apps/plugin-notification').then(async ({ sendNotification, isPermissionGranted, requestPermission }) => {
              let permissionGranted = await isPermissionGranted();
              if (!permissionGranted) {
                const permission = await requestPermission();
                permissionGranted = permission === 'granted';
              }
              if (permissionGranted) {
                const title = data.urgency.toUpperCase() === 'CRITICAL' ? 'Cảnh báo khẩn cấp' : 'Thông báo hệ thống';
                sendNotification({ title: title, body: data.message });
              }
            }).catch(() => {});
          } catch {
            // Ignore if not in Tauri
          }
        } else if (data.type === "error") {
          console.error("Chat Error:", data.content);
          appendStreamChunk(`\n\n**Error:** ${data.content}`);
          commitStream();
        } else if (data.type === "done") {
          commitStream();
        } else if (data.type === "AUTHENTICATED") {
          console.log("WebSocket authenticated!");
        }
      } catch (e) {
        console.error("Error parsing WS message", e);
      }
    };

    ws.current.onclose = () => {
      console.log("WebSocket disconnected, reconnecting in 3s...");
      scheduleReconnect();
    };
  }, [scheduleReconnect]);

  useEffect(() => {
    connectRef.current = connect;
    connect();

    return () => {
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.close();
      }
      if (reconnectTimer.current) {
        window.clearTimeout(reconnectTimer.current);
      }
    };
  }, [connect]);

  const sendMessage = async (content: string) => {
    const chatStore = useChatStore.getState();
    const { addMessage, setStreamingState } = chatStore;
    let targetConversationId = chatStore.activeConversationId;

    if (!targetConversationId) {
      // Lazy Create Conversation
      try {
        const token = useAuthStore.getState().token;
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        const title = content.length > 35 ? content.substring(0, 35) + '...' : content;
        
        const res = await fetch('http://localhost:8000/api/conversations', { 
          method: 'POST', 
          headers,
          body: JSON.stringify({ title })
        });
        
        if (res.ok) {
          const newConv = await res.json();
          targetConversationId = newConv.id;
          chatStore.setConversations([newConv, ...chatStore.conversations]);
          chatStore.setActiveConversation(newConv.id);
        } else {
          console.error("Failed to create conversation lazily");
          return;
        }
      } catch (e) {
        console.error("Error creating conversation", e);
        return;
      }
    }

    addMessage({ id: crypto.randomUUID(), role: 'user', content });
    setStreamingState(true);

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: "chat_message",
        content: content,
        conversation_id: targetConversationId,
        language: localStorage.getItem('app_language') || 'vi'
      }));
    } else {
      console.error("WebSocket is not connected");
      setStreamingState(false);
    }
  };

  const stopGenerating = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: "CANCEL_GENERATION"
      }));
    }
  };

  return { sendMessage, stopGenerating };
};

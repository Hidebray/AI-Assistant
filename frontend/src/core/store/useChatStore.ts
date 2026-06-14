import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

interface ChatState {
  messages: Message[];
  conversations: Conversation[];
  activeConversationId: string | null;
  isStreaming: boolean;
  streamingContent: string;
  addMessage: (msg: Message) => void;
  setMessages: (msgs: Message[]) => void;
  setConversations: (convs: Conversation[]) => void;
  setActiveConversation: (id: string) => void;
  setStreamingState: (isStreaming: boolean) => void;
  appendStreamChunk: (chunk: string) => void;
  commitStream: () => void;
  clearContext: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  conversations: [],
  activeConversationId: null,
  isStreaming: false,
  streamingContent: '',
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setMessages: (msgs) => set({ messages: msgs }),
  setConversations: (convs) => set({ conversations: convs }),
  setActiveConversation: (id) => set({ activeConversationId: id }),
  setStreamingState: (isStreaming) => set({ isStreaming }),
  appendStreamChunk: (chunk) => set((state) => {
    if (!state.isStreaming) return state;
    return { streamingContent: state.streamingContent + chunk };
  }),
  commitStream: () => set((state) => {
    if (!state.streamingContent) {
      return { isStreaming: false };
    }
    const newMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: state.streamingContent
    };
    return {
      messages: [...state.messages, newMessage],
      streamingContent: '',
      isStreaming: false
    };
  }),
  clearContext: () => set({ messages: [], streamingContent: '', isStreaming: false, activeConversationId: null })
}));

import { create } from 'zustand';
import { useAuthStore } from './useAuthStore';

export interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  location: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

interface CalendarState {
  events: CalendarEvent[];
  isLoading: boolean;
  fetchEvents: () => Promise<void>;
  createEvent: (data: { title: string; start_time: string; end_time: string; location?: string }) => Promise<void>;
  deleteEvent: (id: string) => Promise<void>;
}

export const useCalendarStore = create<CalendarState>((set, get) => ({
  events: [],
  isLoading: false,

  fetchEvents: async () => {
    set({ isLoading: true });
    try {
      const token = useAuthStore.getState().token;
      if (!token) return;
      const res = await fetch('http://localhost:8000/api/calendar', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        set({ events: data });
      }
    } catch (e) {
      console.error('Failed to fetch events', e);
    } finally {
      set({ isLoading: false });
    }
  },

  createEvent: async (data) => {
    try {
      const token = useAuthStore.getState().token;
      if (!token) return;
      const res = await fetch('http://localhost:8000/api/calendar', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        const newEvent = await res.json();
        set(state => ({ events: [...state.events, newEvent].sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()) }));
      }
    } catch (e) {
      console.error('Failed to create event', e);
    }
  },

  deleteEvent: async (id) => {
    try {
      const token = useAuthStore.getState().token;
      if (!token) return;

      // Optimistic update
      set(state => ({
        events: state.events.filter(e => e.id !== id)
      }));

      const res = await fetch(`http://localhost:8000/api/calendar/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        get().fetchEvents();
      }
    } catch (e) {
      console.error('Failed to delete event', e);
      get().fetchEvents();
    }
  }
}));

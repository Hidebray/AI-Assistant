import { create } from 'zustand';
import { useAuthStore } from './useAuthStore';

export interface Task {
  id: string;
  title: string;
  description: string | null;
  deadline: string | null;
  status: 'pending' | 'in_progress' | 'completed';
  priority: 'low' | 'medium' | 'high';
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

interface TaskState {
  tasks: Task[];
  isLoading: boolean;
  fetchTasks: () => Promise<void>;
  createTask: (data: { title: string; description?: string; deadline?: string; priority?: string }) => Promise<void>;
  updateTaskStatus: (id: string, status: string) => Promise<void>;
  deleteTask: (id: string) => Promise<void>;
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  isLoading: false,

  fetchTasks: async () => {
    set({ isLoading: true });
    try {
      const token = useAuthStore.getState().token;
      if (!token) return;
      const res = await fetch('http://localhost:8000/api/tasks', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        set({ tasks: data });
      }
    } catch (e) {
      console.error('Failed to fetch tasks', e);
    } finally {
      set({ isLoading: false });
    }
  },

  createTask: async (data) => {
    try {
      const token = useAuthStore.getState().token;
      if (!token) return;
      const res = await fetch('http://localhost:8000/api/tasks', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        const newTask = await res.json();
        set(state => ({ tasks: [newTask, ...state.tasks] }));
      }
    } catch (e) {
      console.error('Failed to create task', e);
    }
  },

  updateTaskStatus: async (id, status) => {
    try {
      const token = useAuthStore.getState().token;
      if (!token) return;
      
      // Optimistic update
      set(state => ({
        tasks: state.tasks.map(t => t.id === id ? { ...t, status: status as any } : t)
      }));

      const res = await fetch(`http://localhost:8000/api/tasks/${id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status })
      });
      if (!res.ok) {
        // Rollback on fail
        get().fetchTasks();
      }
    } catch (e) {
      console.error('Failed to update task', e);
      get().fetchTasks();
    }
  },

  deleteTask: async (id) => {
    try {
      const token = useAuthStore.getState().token;
      if (!token) return;

      // Optimistic update
      set(state => ({
        tasks: state.tasks.filter(t => t.id !== id)
      }));

      const res = await fetch(`http://localhost:8000/api/tasks/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        get().fetchTasks();
      }
    } catch (e) {
      console.error('Failed to delete task', e);
      get().fetchTasks();
    }
  }
}));

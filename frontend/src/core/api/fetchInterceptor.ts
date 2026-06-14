import { useAuthStore } from '../store/useAuthStore';
import { useAlertStore } from '../store/useAlertStore';

const originalFetch = window.fetch;

window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
  try {
    let url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
    
    // Convert relative API calls to absolute URLs pointing to the backend
    // This is required when running inside Tauri since the origin is tauri://localhost
    if (url.startsWith('/api/')) {
      url = `http://localhost:8000${url}`;
      input = url;
    }

    const response = await originalFetch(input, init);
    
    // Check for 401 Unauthorized
    if (response.status === 401) {
      // Don't auto-logout if we are already trying to login/register
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
      if (!url.includes('/api/auth/login') && !url.includes('/api/auth/register')) {
        const { logout } = useAuthStore.getState();
        const { triggerAlert } = useAlertStore.getState();
        
        triggerAlert({
          urgency: 'high',
          title: 'Phiên bản hết hạn',
          message: 'Tài khoản của bạn đã hết phiên đăng nhập hoặc bị đăng xuất từ nơi khác. Vui lòng đăng nhập lại.'
        });
        
        logout();
      }
    }
    
    return response;
  } catch (error) {
    throw error;
  }
};

import { useState } from 'react';
import { useAuthStore } from '../../core/store/useAuthStore';
import type { LoginFormValues, RegisterFormValues } from '../../core/schemas/auth.schema';

interface AuthResponse {
  access_token: string;
}

interface ErrorResponse {
  detail?: string;
}

const getErrorMessage = (err: unknown) => err instanceof Error ? err.message : 'Đã xảy ra lỗi';

export const useAuth = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setToken = useAuthStore(state => state.setToken);

  const login = async (data: LoginFormValues) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: data.username, password: data.password })
      });
      const result = await response.json() as AuthResponse & ErrorResponse;
      if (!response.ok) {
        throw new Error(result.detail || 'Đăng nhập thất bại');
      }
      setToken(result.access_token);
      return "success";
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterFormValues) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: data.username, password: data.password })
      });
      const result = await response.json() as AuthResponse & ErrorResponse;
      if (!response.ok) {
        throw new Error(result.detail || 'Đăng ký thất bại');
      }
      setToken(result.access_token);
      return "success";
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { login, register, isLoading, error };
};

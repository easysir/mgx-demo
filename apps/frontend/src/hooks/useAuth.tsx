'use client';

import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { fetchProfile, login } from '@/lib/api/chat';
import type { UserProfile } from '@/types/chat';

interface AuthContextValue {
  user: UserProfile | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? window.localStorage.getItem('mgx-token') : null;
    if (stored) {
      setToken(stored);
      fetchProfile(stored)
        .then(setUser)
        .catch(() => {
          setToken(null);
          window.localStorage.removeItem('mgx-token');
        });
    }
  }, []);

  const loginHandler = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await login(email, password);
      setToken(resp.access_token);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('mgx-token', resp.access_token);
      }
      const profile = await fetchProfile(resp.access_token);
      setUser(profile);
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败');
      setToken(null);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem('mgx-token');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('mgx-token');
    }
  };

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, login: loginHandler, logout, loading, error }),
    [user, token, loading, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}

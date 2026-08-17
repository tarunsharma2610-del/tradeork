"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api, type AuthTokens, type User } from "./api";

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName?: string
  ) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    const t = await api.login({ email, password });
    setTokens(t);
    setUser(await api.me(t.access_token));
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const t = await api.register({ email, password, full_name: fullName });
      setTokens(t);
      setUser(await api.me(t.access_token));
    },
    []
  );

  const logout = useCallback(async () => {
    if (tokens) {
      try {
        await api.logout(tokens.refresh_token);
      } catch {
        // already invalid server-side; clear locally regardless
      }
    }
    setTokens(null);
    setUser(null);
  }, [tokens]);

  const value = useMemo(
    () => ({ user, tokens, login, register, logout }),
    [user, tokens, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}

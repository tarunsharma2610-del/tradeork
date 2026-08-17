"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api, type AuthTokens, type User } from "./api";

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  /** True while the httpOnly refresh cookie is being checked on startup. */
  restoring: boolean;
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
  const [restoring, setRestoring] = useState(true);

  // Restore a logged-in session from the httpOnly refresh cookie, which the
  // SPA cannot read directly but is sent automatically on same-origin
  // requests to the proxied /api/* path.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const t = await api.refresh();
        if (cancelled) return;
        setTokens(t);
        setUser(await api.me(t.access_token));
      } catch {
        // No valid session cookie; stay signed out.
      } finally {
        if (!cancelled) setRestoring(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

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
    try {
      await api.logout();
    } catch {
      // already invalid server-side; clear locally regardless
    }
    setTokens(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, tokens, restoring, login, register, logout }),
    [user, tokens, restoring, login, register, logout]
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

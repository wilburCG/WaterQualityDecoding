"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type AuthUser = {
  id: number;
  email: string | null;
  display_name: string;
  role: string;
};

type AuthContextType = {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => void;
};

const TOKEN_KEY = "wqd_token";

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function fetchMe(t: string) {
    const res = await fetch("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${t}` },
    });
    if (res.ok) {
      setUser(await res.json());
    } else {
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
    }
  }

  useEffect(() => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (t) {
      setToken(t);
      fetchMe(t).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function handleAuth(res: Response) {
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "请求失败");
    }
    const data = await res.json();
    localStorage.setItem(TOKEN_KEY, data.token);
    setToken(data.token);
    setUser(data.user);
  }

  const login = async (email: string, password: string) => {
    await handleAuth(
      await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      }),
    );
  };

  const register = async (email: string, password: string, displayName: string) => {
    await handleAuth(
      await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, display_name: displayName }),
      }),
    );
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

/** 带登录态的 fetch；默认带 Bearer token。 */
export async function apiFetch(
  url: string,
  token: string | null,
  options: RequestInit = {},
) {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body) headers.set("Content-Type", "application/json");
  return fetch(url, { ...options, headers });
}

"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type AuthUser = {
  id: number;
  email: string | null;
  phone: string | null;
  display_name: string;
  role: string;
};

type AuthContextType = {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  phoneAuth: (phone: string, displayName: string) => Promise<void>;
  adminLogin: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const TOKEN_KEY = "***";

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) {
      setLoading(false);
      return;
    }
    setToken(t);
    fetch("/api/v1/auth/me", { headers: { Authorization: `Bearer ${t}` } })
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleAuth(res: Response) {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "请求失败");
    localStorage.setItem(TOKEN_KEY, data.token);
    setToken(data.token);
    setUser(data.user);
  }

  const phoneAuth = async (phone: string, displayName: string) => {
    await handleAuth(
      await fetch("/api/v1/auth/phone", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, display_name: displayName }),
      }),
    );
  };

  const adminLogin = async (email: string, password: string) => {
    await handleAuth(
      await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      }),
    );
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, phoneAuth, adminLogin, logout }}>
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

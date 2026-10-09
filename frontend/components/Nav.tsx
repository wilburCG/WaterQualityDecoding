"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch, useAuth } from "@/lib/auth";

const links = [
  { href: "/", label: "首页" },
  { href: "/decode", label: "报告解码" },
  { href: "/indicators", label: "指标百科" },
  { href: "/cases/tongfenjing", label: "案例：同汾泾" },
  { href: "/map", label: "河流地图" },
  { href: "/ask", label: "知识问答" },
];

export default function Nav() {
  const pathname = usePathname();
  const { user, logout, token } = useAuth();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!token) {
      setUnread(0);
      return;
    }
    let active = true;
    const tick = async () => {
      try {
        const res = await apiFetch("/api/v1/notifications/unread-count", token);
        if (res.ok && active) {
          const data = await res.json();
          setUnread(data.unread);
        }
      } catch {
        /* ignore */
      }
    };
    tick();
    const timer = setInterval(tick, 60_000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [token, pathname]);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-1 overflow-x-auto px-4">
        <Link href="/" className="mr-3 flex shrink-0 items-center gap-2 font-bold text-brand">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-sm text-white">
            水
          </span>
          <span className="hidden sm:inline">水质解码器</span>
        </Link>
        {links.slice(1).map((l) => {
          const active = pathname === l.href;
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`shrink-0 rounded-full px-3 py-1.5 text-sm ${
                active ? "bg-brand-light text-brand" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {l.label}
            </Link>
          );
        })}

        <div className="ml-auto flex shrink-0 items-center gap-2 pl-2">
          {user?.role === "admin" && (
            <Link
              href="/admin"
              className={`rounded-full px-3 py-1.5 text-sm ${
                pathname === "/admin"
                  ? "bg-brand-light text-brand"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              审核后台
            </Link>
          )}
          {user ? (
            <>
              <Link
                href="/subscriptions"
                className={`rounded-full px-3 py-1.5 text-sm ${
                  pathname === "/subscriptions"
                    ? "bg-brand-light text-brand"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                我的订阅
              </Link>
              <Link
                href="/notifications"
                title="通知中心"
                className={`relative rounded-full px-2 py-1.5 text-sm ${
                  pathname === "/notifications"
                    ? "bg-brand-light text-brand"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                🔔
                {unread > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-semibold text-white">
                    {unread > 99 ? "99+" : unread}
                  </span>
                )}
              </Link>
              <Link
                href="/submissions"
                className="max-w-[8rem] truncate rounded-full px-2 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
                title={user.email ?? user.display_name}
              >
                {user.display_name}
              </Link>
              <button
                onClick={logout}
                className="rounded-full border border-slate-300 px-3 py-1 text-xs text-slate-600"
              >
                退出
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="rounded-full bg-brand px-4 py-1.5 text-sm text-white"
            >
              登录 / 注册
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

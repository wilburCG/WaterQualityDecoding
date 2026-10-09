"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, useAuth } from "@/lib/auth";

type Notice = {
  id: number;
  kind: string;
  title: string;
  body: string;
  link: string;
  is_read: boolean;
  created_at: string;
};

const KIND_STYLE: Record<string, string> = {
  grade_alert: "border-amber-200 bg-amber-50",
  new_data: "border-sky-200 bg-sky-50",
  system: "border-slate-200 bg-slate-50",
};

export default function NotificationsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Notice[] | null>(null);
  const [unread, setUnread] = useState(0);

  async function load() {
    if (!token) return;
    const res = await apiFetch("/api/v1/notifications", token);
    if (res.ok) {
      const data = await res.json();
      setItems(data.items);
      setUnread(data.unread);
    }
  }

  useEffect(() => {
    load();
  }, [token]);

  async function markAll() {
    await apiFetch("/api/v1/notifications/read", token, { method: "POST" });
    await load();
  }

  async function markOne(n: Notice) {
    await apiFetch("/api/v1/notifications/read", token, {
      method: "POST",
      body: JSON.stringify({ ids: [n.id] }),
    });
    await load();
  }

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">通知中心</h1>
          <p className="mt-1 text-sm text-slate-500">
            {unread > 0 ? `你有 ${unread} 条未读通知` : "所有通知都已读"}
          </p>
        </div>
        {unread > 0 && (
          <button
            onClick={markAll}
            className="rounded-full border border-slate-300 px-4 py-1.5 text-xs text-slate-600"
          >
            全部标为已读
          </button>
        )}
      </div>

      {items === null ? (
        <p className="text-sm text-slate-400">加载中…</p>
      ) : items.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-slate-300 bg-white px-8 py-12 text-center text-sm text-slate-500">
          还没有通知。订阅关心的河流后，有新数据或水质预警会出现在这里。
          <br />
          <Link href="/subscriptions" className="mt-3 inline-block text-brand underline">
            去订阅河流
          </Link>
        </p>
      ) : (
        items.map((n) => (
          <div
            key={n.id}
            className={`rounded-2xl border p-4 ${KIND_STYLE[n.kind] || KIND_STYLE.system} ${
              n.is_read ? "opacity-60" : ""
            }`}
          >
            <div className="flex items-start gap-2">
              {!n.is_read && (
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand" />
              )}
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-800">{n.title}</p>
                <p className="mt-1 text-xs leading-5 text-slate-600">{n.body}</p>
                <p className="mt-2 text-[11px] text-slate-400">
                  {new Date(n.created_at).toLocaleString("zh-CN")}
                </p>
                <div className="mt-2 flex gap-3 text-xs">
                  {n.link && (
                    <Link
                      href={n.link}
                      onClick={() => !n.is_read && markOne(n)}
                      className="text-brand underline"
                    >
                      查看详情
                    </Link>
                  )}
                  {!n.is_read && (
                    <button
                      onClick={() => markOne(n)}
                      className="text-slate-500 underline"
                    >
                      标为已读
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

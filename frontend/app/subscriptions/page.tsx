"use client";

import { useEffect, useState } from "react";
import { apiFetch, useAuth } from "@/lib/auth";

type KnownRiver = { river: string; sample_count: number; subscribed: boolean };
type MySub = {
  id: number;
  target_type: string;
  target_key: string;
  target_label: string;
  alert_grade_from: number;
};

const ALERT_OPTIONS = [
  { value: 3, label: "Ⅲ类及以上都提醒（含Ⅲ类）" },
  { value: 4, label: "仅 Ⅳ 类及以下预警" },
  { value: 5, label: "仅 Ⅴ 类及以下预警" },
];

export default function SubscriptionsPage() {
  const { token } = useAuth();
  const [rivers, setRivers] = useState<KnownRiver[] | null>(null);
  const [subs, setSubs] = useState<MySub[] | null>(null);
  const [customRiver, setCustomRiver] = useState("");
  const [msg, setMsg] = useState("");

  async function load() {
    if (!token) return;
    const [r1, r2] = await Promise.all([
      apiFetch("/api/v1/rivers", token),
      apiFetch("/api/v1/subscriptions", token),
    ]);
    if (r1.ok) setRivers(await r1.json());
    if (r2.ok) setSubs(await r2.json());
  }

  useEffect(() => {
    load();
  }, [token]);

  async function subscribe(river: string) {
    const res = await apiFetch("/api/v1/subscriptions", token, {
      method: "POST",
      body: JSON.stringify({ target_type: "river", target_key: river }),
    });
    const data = await res.json().catch(() => ({}));
    setMsg(res.ok ? `已订阅「${river}」` : data.detail || "订阅失败");
    await load();
  }

  async function unsubscribe(s: MySub) {
    const res = await apiFetch(`/api/v1/subscriptions/${s.id}`, token, {
      method: "DELETE",
    });
    if (res.ok) {
      setMsg(`已取消订阅「${s.target_label}」`);
      await load();
    }
  }

  async function changeAlertLevel(s: MySub, level: number) {
    // 先删后建，保持简单
    await apiFetch(`/api/v1/subscriptions/${s.id}`, token, { method: "DELETE" });
    await apiFetch("/api/v1/subscriptions", token, {
      method: "POST",
      body: JSON.stringify({
        target_type: s.target_type,
        target_key: s.target_key,
        target_label: s.target_label,
        alert_grade_from: level,
      }),
    });
    await load();
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">我的订阅</h1>
        <p className="mt-1 text-sm text-slate-500">
          订阅河流后，该河流有新的审核通过数据会通知你；水质较差时额外发出预警。
        </p>
      </div>

      {msg && (
        <p className="rounded-lg bg-brand-light px-3 py-2 text-xs text-brand">
          {msg}
        </p>
      )}

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-800">已订阅（{subs?.length ?? 0}）</h2>
        {subs === null ? (
          <p className="mt-3 text-sm text-slate-400">加载中…</p>
        ) : subs.length === 0 ? (
          <p className="mt-3 text-xs text-slate-400">
            还没有订阅，从下面的河流列表选择吧。
          </p>
        ) : (
          <div className="mt-3 space-y-3">
            {subs.map((s) => (
              <div
                key={s.id}
                className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 px-3 py-2.5"
              >
                <span className="text-sm text-slate-700">
                  {s.target_type === "river" ? "🏞️" : "📍"} {s.target_label}
                </span>
                <select
                  value={s.alert_grade_from}
                  onChange={(e) => changeAlertLevel(s, Number(e.target.value))}
                  className="ml-1 rounded-md border border-slate-300 px-2 py-1 text-[11px] text-slate-600"
                >
                  {ALERT_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => unsubscribe(s)}
                  className="ml-auto text-xs text-red-500"
                >
                  取消订阅
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-800">可订阅的河流</h2>
        {rivers === null ? (
          <p className="mt-3 text-sm text-slate-400">加载中…</p>
        ) : rivers.length === 0 ? (
          <p className="mt-3 text-xs text-slate-400">暂时没有含公开数据的河流。</p>
        ) : (
          <div className="mt-3 space-y-2">
            {rivers.map((r) => (
              <div
                key={r.river}
                className="flex items-center gap-3 rounded-xl border border-slate-200 px-3 py-2.5"
              >
                <span className="text-sm text-slate-700">{r.river}</span>
                <span className="text-[11px] text-slate-400">
                  {r.sample_count} 份公开数据
                </span>
                <button
                  onClick={() => subscribe(r.river)}
                  disabled={r.subscribed}
                  className="ml-auto rounded-full px-4 py-1 text-xs text-white disabled:bg-slate-300 enabled:bg-brand"
                >
                  {r.subscribed ? "已订阅" : "订阅"}
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="mt-4 flex gap-2 border-t border-slate-100 pt-4">
          <input
            value={customRiver}
            onChange={(e) => setCustomRiver(e.target.value)}
            placeholder="也可以输入其他河流名称订阅"
            className="flex-1 rounded-full border border-slate-300 px-4 py-2 text-sm"
          />
          <button
            onClick={() => customRiver.trim() && subscribe(customRiver.trim())}
            className="rounded-full border border-brand px-4 py-2 text-xs text-brand"
          >
            订阅
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";
import { GRADE_COLORS, METHOD_LEVELS } from "@/lib/types";
import { apiFetch, useAuth } from "@/lib/auth";

type AdminRow = {
  id: number;
  sampled_at: string;
  submitted_at: string;
  method_level: number;
  method_note: string;
  overall_grade: number | null;
  deciding_factors: string[];
  review_status: string;
  review_note: string;
  contributor: string | null;
  site: { name: string; river: string; lng: number; lat: number };
  measurements: { code: string; value: number; grade: number | null }[];
};

const TABS = [
  { value: "pending", label: "待审核" },
  { value: "approved", label: "已通过" },
  { value: "rejected", label: "已驳回" },
] as const;

export default function AdminPage() {
  const { user, token } = useAuth();
  const [tab, setTab] = useState<string>("pending");
  const [rows, setRows] = useState<AdminRow[] | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setRows(null);
    const res = await apiFetch(`/api/v1/admin/samples?status=${tab}`, token);
    setRows(await res.json());
  }, [token, tab]);

  useEffect(() => {
    load();
  }, [load]);

  async function moderate(id: number, action: "approve" | "reject") {
    let note = "";
    if (action === "reject") {
      note = window.prompt("请填写驳回理由（将展示给提交者）") ?? "";
      if (!note.trim()) return;
    }
    setBusyId(id);
    try {
      const res = await apiFetch(
        `/api/v1/admin/samples/${id}/${action}`, token,
        { method: "POST", body: action === "reject" ? JSON.stringify({ note }) : undefined },
      );
      if (!res.ok) {
        alert("操作失败");
        return;
      }
      await load();
    } finally {
      setBusyId(null);
    }
  }

  if (!user) {
    return <p className="text-sm text-slate-400">请先登录管理员账号。</p>;
  }
  if (user.role !== "admin") {
    return <p className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
      403：当前账号没有管理员权限。
    </p>;
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">审核后台</h1>
      <p className="text-xs text-slate-400">
        众包数据先审后发：仅通过审核的分享会出现在公开地图。审核请核对点位合理性、数据完整性与可信度。
      </p>

      <div className="flex gap-2">
        {TABS.map((t) => (
          <button key={t.value} onClick={() => setTab(t.value)}
            className={`rounded-full px-4 py-1.5 text-sm ${
              tab === t.value ? "bg-brand text-white" : "border border-slate-300 text-slate-600"
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {rows === null ? (
        <p className="text-sm text-slate-400">加载中…</p>
      ) : rows.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-slate-300 bg-white px-8 py-14 text-center text-sm text-slate-500">
          暂无数据
        </p>
      ) : (
        rows.map((s) => {
          const color = s.overall_grade ? GRADE_COLORS[s.overall_grade] : "#94a3b8";
          return (
            <div key={s.id} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5">
              <div className="flex flex-wrap items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold text-white"
                      style={{ backgroundColor: color }}>
                  {s.overall_grade === 6 ? "劣Ⅴ" : `${s.overall_grade ?? "-"}`}
                </span>
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    {s.site.river ? `${s.site.river} · ` : ""}{s.site.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    采样 {new Date(s.sampled_at).toLocaleString("zh-CN")} ·
                    提交 {new Date(s.submitted_at).toLocaleString("zh-CN")} ·
                    提交者 {s.contributor ?? "匿名"}
                  </p>
                </div>
                <span className="ml-auto text-xs text-slate-400">
                  {s.site.lng.toFixed(4)}, {s.site.lat.toFixed(4)}
                </span>
              </div>

              <div className="flex flex-wrap gap-2 text-xs">
                {s.measurements.map((m) => (
                  <span key={m.code} className="rounded-full bg-slate-100 px-3 py-1 text-slate-600">
                    {m.code}: <b>{m.value}</b>
                  </span>
                ))}
              </div>

              <p className="text-xs text-slate-500">
                {METHOD_LEVELS.find((m) => m.value === s.method_level)?.label}
                {s.method_note ? ` · ${s.method_note}` : ""}
                {s.deciding_factors.length ? ` · 定类因子：${s.deciding_factors.join("、")}` : ""}
              </p>

              {s.review_status === "rejected" && s.review_note && (
                <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
                  驳回理由：{s.review_note}
                </p>
              )}

              {tab === "pending" && (
                <div className="flex gap-3 pt-1">
                  <button onClick={() => moderate(s.id, "approve")} disabled={busyId === s.id}
                    className="rounded-full bg-green-600 px-5 py-2 text-xs font-medium text-white disabled:opacity-50">
                    通过
                  </button>
                  <button onClick={() => moderate(s.id, "reject")} disabled={busyId === s.id}
                    className="rounded-full border border-red-300 px-5 py-2 text-xs text-red-600 disabled:opacity-50">
                    驳回
                  </button>
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}

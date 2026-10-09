"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { GRADE_COLORS, METHOD_LEVELS } from "@/lib/types";
import { apiFetch, useAuth } from "@/lib/auth";

type SampleRow = {
  id: number;
  sampled_at: string;
  method_level: number;
  overall_grade: number | null;
  deciding_factors: string[];
  review_status: string;
  review_note: string;
  site: { name: string; river: string };
  measurements: { code: string; value: number }[];
};

const STATUS_LABEL: Record<string, { text: string; cls: string }> = {
  pending: { text: "待审核", cls: "bg-amber-100 text-amber-700" },
  approved: { text: "已发布", cls: "bg-green-100 text-green-700" },
  rejected: { text: "未通过", cls: "bg-red-100 text-red-700" },
};

export default function MySubmissions() {
  const { user, token } = useAuth();
  const [rows, setRows] = useState<SampleRow[] | null>(null);

  useEffect(() => {
    if (!token) {
      setRows([]);
      return;
    }
    apiFetch("/api/v1/samples/mine", token)
      .then((r) => r.json())
      .then(setRows);
  }, [token]);

  if (!user) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-8 py-16 text-center text-sm text-slate-500">
        请先<Link href="/login" className="text-brand">登录</Link>后查看自己的提交。
      </div>
    );
  }

  if (rows === null) {
    return <p className="text-sm text-slate-400">加载中…</p>;
  }

  if (rows.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-8 py-16 text-center text-sm text-slate-500">
        还没有提交过检测数据，去
        <Link href="/decode" className="text-brand">报告解码</Link>生成体检报告并发布吧。
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">我的提交</h1>
      {rows.map((s) => {
        const st = STATUS_LABEL[s.review_status];
        const color = s.overall_grade ? GRADE_COLORS[s.overall_grade] : "#94a3b8";
        const methodLabel = METHOD_LEVELS.find((m) => m.value === s.method_level)?.label;
        return (
          <div key={s.id} className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex flex-wrap items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold text-white"
                    style={{ backgroundColor: color }}>
                {s.overall_grade === 6 ? "劣Ⅴ" : `${s.overall_grade ?? "-"}`}
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-800">
                  {s.site.river ? `${s.site.river} · ` : ""}{s.site.name}
                </p>
                <p className="text-xs text-slate-400">
                  {new Date(s.sampled_at).toLocaleString("zh-CN")} · {methodLabel}
                </p>
              </div>
              <span className={`ml-auto rounded-full px-3 py-1 text-xs ${st.cls}`}>
                {st.text}
              </span>
            </div>

            {s.deciding_factors.length > 0 && (
              <p className="mt-3 text-xs text-slate-500">
                定类因子：{s.deciding_factors.join("、")}
              </p>
            )}
            {s.review_status === "rejected" && s.review_note && (
              <p className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
                审核意见：{s.review_note}
              </p>
            )}
            {s.review_status === "approved" && (
              <Link href="/map" className="mt-2 inline-block text-xs text-brand">
                查看地图 →
              </Link>
            )}
          </div>
        );
      })}
    </div>
  );
}

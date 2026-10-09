"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { SiteGroup } from "@/components/LeafletMap";
import { GRADE_COLORS, METHOD_LEVELS } from "@/lib/types";

// Leaflet 依赖 window，仅客户端加载
const LeafletMap = dynamic(() => import("@/components/LeafletMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 text-sm text-slate-400">
      地图加载中…
    </div>
  ),
});

type PublicSample = {
  id: number;
  sampled_at: string;
  method_level: number;
  overall_grade: number | null;
  site: { id: number; name: string; river: string; lng: number; lat: number };
};

const GRADE_FILTERS = [
  { value: 0, label: "全部类别" },
  { value: 1, label: "Ⅰ" },
  { value: 2, label: "Ⅱ" },
  { value: 3, label: "Ⅲ" },
  { value: 4, label: "Ⅳ" },
  { value: 5, label: "Ⅴ" },
  { value: 6, label: "劣Ⅴ" },
];

export default function MapPage() {
  const [rows, setRows] = useState<PublicSample[] | null>(null);
  const [grade, setGrade] = useState(0);
  const [method, setMethod] = useState(0);
  const [focusKey, setFocusKey] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/v1/samples")
      .then((r) => r.json())
      .then(setRows);
  }, []);

  const filtered = useMemo(() => {
    if (!rows) return [];
    return rows.filter(
      (s) =>
        (grade === 0 || s.overall_grade === grade) &&
        (method === 0 || s.method_level === method),
    );
  }, [rows, grade, method]);

  // 同一点位聚合为时间轴（最新类别决定气泡颜色）
  const groups: SiteGroup[] = useMemo(() => {
    const map = new Map<string, SiteGroup>();
    for (const s of filtered) {
      const key = `${s.site.id}`;
      if (!map.has(key)) {
        map.set(key, {
          key,
          name: s.site.name,
          river: s.site.river,
          lng: s.site.lng,
          lat: s.site.lat,
          latestGrade: s.overall_grade ?? 0,
          samples: [],
        });
      }
      map.get(key)!.samples.push({
        id: s.id,
        sampledAt: s.sampled_at,
        grade: s.overall_grade,
      });
    }
    return [...map.values()].map((g) => ({
      ...g,
      samples: g.samples.sort(
        (a, b) => +new Date(a.sampledAt) - +new Date(b.sampledAt),
      ),
    }));
  }, [filtered]);

  const focus = groups.find((g) => g.key === focusKey) ?? null;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">众包河流地图</h1>
        <p className="mt-1 text-xs text-slate-500">
          ⚠️ 以下数据为公民科学分享，<b>仅供科普参考，非官方监测结论</b>。
          全部数据先审后发，按检测方式标注可信度。
        </p>
      </div>

      <div className="flex flex-wrap gap-3 text-sm">
        <select
          className="rounded-lg border border-slate-300 px-3 py-1.5"
          value={grade}
          onChange={(e) => setGrade(Number(e.target.value))}
        >
          {GRADE_FILTERS.map((g) => (
            <option key={g.value} value={g.value}>{g.label}</option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slate-300 px-3 py-1.5"
          value={method}
          onChange={(e) => setMethod(Number(e.target.value))}
        >
          <option value={0}>全部检测方式</option>
          {METHOD_LEVELS.map((m) => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
        <Link
          href="/decode"
          className="ml-auto rounded-full bg-brand px-4 py-1.5 text-xs text-white"
        >
          + 分享我的检测
        </Link>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_18rem]">
        <LeafletMap groups={groups} focus={focus} />

        <div className="max-h-[520px] space-y-2 overflow-y-auto pr-1">
          {rows === null ? (
            <p className="text-sm text-slate-400">加载中…</p>
          ) : groups.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-xs text-slate-400">
              当前筛选下暂无数据
            </p>
          ) : (
            groups.map((g) => (
              <button
                key={g.key}
                onClick={() => setFocusKey(g.key)}
                className={`w-full rounded-xl border bg-white p-3 text-left text-sm ${
                  focusKey === g.key ? "border-brand" : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="h-3 w-3 shrink-0 rounded-full"
                    style={{ backgroundColor: GRADE_COLORS[g.latestGrade] ?? "#94a3b8" }}
                  />
                  <span className="truncate text-slate-800">
                    {g.river ? `${g.river} · ` : ""}{g.name}
                  </span>
                </div>
                <p className="mt-1 pl-5 text-xs text-slate-400">
                  {g.samples.length} 次分享 ·
                  最新 {new Date(g.samples[g.samples.length - 1].sampledAt).toLocaleDateString("zh-CN")}
                </p>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

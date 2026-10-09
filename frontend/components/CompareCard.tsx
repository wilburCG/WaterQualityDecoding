"use client";

import { useState } from "react";

type CompareItem = {
  code: string;
  label: string;
  unit: string;
  citizen: number;
  official: number;
  diff: number;
  rel_diff_pct: number | null;
};

type Match = {
  section: {
    code: string;
    name: string;
    river: string;
    level: string;
    source_org: string;
  };
  reading: {
    observed_at: string;
    source: string;
    note: string;
    overall_grade: number | null;
  };
  distance_km: number;
  days_gap: number;
  items: CompareItem[];
};

export default function CompareCard({
  lng,
  lat,
  sampledAt,
  values,
}: {
  lng: number | null;
  lat: number | null;
  sampledAt: string;
  values: Record<string, number>;
}) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">(
    "idle",
  );
  const [matches, setMatches] = useState<Match[]>([]);
  const [caveat, setCaveat] = useState("");
  const [emptyNote, setEmptyNote] = useState("");

  async function runCompare() {
    if (lng === null || lat === null) {
      setState("error");
      return;
    }
    setState("loading");
    try {
      const res = await fetch("/api/v1/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lng,
          lat,
          sampled_at: new Date(sampledAt || Date.now()).toISOString(),
          values,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "对照失败");
      setMatches(data.matches);
      setCaveat(data.caveat);
      setEmptyNote(data.empty_note || "");
      setState("done");
    } catch {
      setState("error");
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="text-sm font-semibold text-slate-800">
        📊 与附近官方监测断面对照
      </h2>
      <p className="mt-1 text-xs leading-5 text-slate-500">
        按位置（默认 8 公里内）和时间（前后 3 周）匹配已收录的官方断面读数，逐指标比较差异。
      </p>

      {state === "idle" && (
        <button
          onClick={runCompare}
          className="mt-4 rounded-full border border-brand px-5 py-2 text-sm text-brand"
        >
          开始对照
        </button>
      )}

      {state === "loading" && (
        <p className="mt-4 text-sm text-slate-400">正在匹配附近官方断面…</p>
      )}

      {state === "error" && (
        <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
          {lng === null || lat === null
            ? "对照需要点位经纬度：请先在上方填写经度、纬度和采样时间。"
            : "对照失败，请稍后重试。"}
        </p>
      )}

      {state === "done" && matches.length === 0 && (
        <p className="mt-4 rounded-lg bg-slate-50 px-3 py-3 text-xs leading-6 text-slate-500">
          {emptyNote}
        </p>
      )}

      {state === "done" && matches.length > 0 && (
        <div className="mt-4 space-y-4">
          {matches.map((m) => (
            <div key={m.section.code} className="rounded-xl border border-slate-200 p-4">
              <div className="flex flex-wrap items-baseline gap-x-2">
                <span className="text-sm font-medium text-slate-800">
                  《{m.section.name}》
                </span>
                <span className="text-[11px] text-slate-400">
                  {m.section.level}断面 · {m.section.source_org}
                </span>
                <span className="ml-auto text-[11px] text-slate-400">
                  相距 {m.distance_km} km · 时间差 {m.days_gap} 天
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-400">
                官方读数日期：{m.reading.observed_at.slice(0, 10)} ·{" "}
                {m.reading.source}
                {m.reading.note ? ` · ${m.reading.note}` : ""}
              </p>

              <div className="mt-3 space-y-1.5">
                {m.items.map((it) => (
                  <div
                    key={it.code}
                    className="flex items-center gap-2 text-xs text-slate-600"
                  >
                    <span className="w-24 shrink-0 text-slate-500">
                      {it.label}
                    </span>
                    <span className="w-16 text-right">{it.citizen}</span>
                    <span className="text-slate-300">vs</span>
                    <span className="w-16">{it.official}</span>
                    <span
                      className={`ml-1 rounded px-1.5 py-0.5 text-[10px] ${
                        it.rel_diff_pct !== null && it.rel_diff_pct > 30
                          ? "bg-amber-100 text-amber-700"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      差 {it.diff > 0 ? "+" : ""}{it.diff} {it.unit}{it.rel_diff_pct !== null ? ` (${it.rel_diff_pct}%)` : ""}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
          <p className="rounded-lg bg-slate-50 px-3 py-2 text-[11px] leading-5 text-slate-500">
            ⚠️ {caveat}
          </p>
        </div>
      )}
    </div>
  );
}

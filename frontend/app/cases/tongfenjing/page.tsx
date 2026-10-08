"use client";

import { useEffect, useState } from "react";
import { GRADE_COLORS } from "@/lib/types";

type Measurement = { code: string; value: number; grade: number | null };
type CaseSample = {
  sample_id: number;
  sampled_at: string;
  site_name: string;
  method_level: number;
  overall_grade: number;
  deciding_factors: string[];
  measurements: Measurement[];
};

type CaseData = {
  narrative: {
    title: string;
    river: string;
    authors: string;
    intro: string;
    mechanisms: { name: string; text: string }[];
  };
  samples: CaseSample[];
};

const INDICATOR_NAMES: Record<string, string> = {
  tp: "总磷",
  tn: "总氮",
  nh3n: "氨氮",
  codmn: "高锰酸盐指数",
};

export default function CasePage() {
  const [data, setData] = useState<CaseData | null>(null);

  useEffect(() => {
    fetch("/api/v1/cases/tongfenjing")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return <p className="text-slate-400">加载中…</p>;
  const n = data.narrative;

  return (
    <div className="space-y-8">
      <header>
        <p className="text-xs tracking-widest text-brand">公开案例 #1 · CASE STUDY</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-800">{n.title}</h1>
        <p className="mt-2 text-sm text-slate-500">{n.river}</p>
        <p className="mt-1 text-xs text-slate-400">公民科学参与者：{n.authors}（隐名）</p>
        <p className="mt-4 text-sm leading-7 text-slate-600">{n.intro}</p>
      </header>

      <section className="grid gap-4 sm:grid-cols-3">
        {n.mechanisms.map((m, i) => (
          <div key={m.name} className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-light text-sm font-bold text-brand">
              {i + 1}
            </div>
            <h2 className="mt-3 font-semibold text-slate-800">{m.name}</h2>
            <p className="mt-2 text-sm leading-7 text-slate-600">{m.text}</p>
          </div>
        ))}
      </section>

      <section>
        <h2 className="text-lg font-semibold text-slate-800">实测数据</h2>
        <p className="mt-1 text-xs text-slate-400">
          水样由专业实验室全自动分析仪分析（可信度①），评价依据 GB 3838-2002。
        </p>
        <div className="mt-4 space-y-4">
          {data.samples.map((s) => (
            <div key={s.sample_id} className="overflow-hidden rounded-xl border border-slate-200 bg-white">
              <div className="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
                <div>
                  <span className="font-medium text-slate-800">{s.site_name}</span>
                  <span className="ml-2 text-xs text-slate-400">
                    {new Date(s.sampled_at).toLocaleString("zh-CN")}
                  </span>
                </div>
                <span
                  className="rounded-md px-2.5 py-1 text-xs font-medium text-white"
                  style={{ background: GRADE_COLORS[s.overall_grade] }}
                >
                  {s.overall_grade === 6 ? "劣Ⅴ" : ["", "Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ"][s.overall_grade]} 类
                  {s.deciding_factors.length > 0 &&
                    `（定类：${s.deciding_factors.map((f) => INDICATOR_NAMES[f] || f).join("、")}）`}
                </span>
              </div>
              <div className="grid gap-2 border-t border-slate-100 px-5 py-3 sm:grid-cols-4">
                {s.measurements.map((m) => (
                  <div key={m.code} className="text-sm">
                    <span className="text-slate-500">{INDICATOR_NAMES[m.code] || m.code}</span>
                    <div className="font-medium text-slate-800">{m.value} mg/L</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

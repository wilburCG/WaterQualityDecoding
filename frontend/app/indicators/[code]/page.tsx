"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { GRADE_COLORS } from "@/lib/types";

type Detail = {
  code: string;
  name: string;
  unit: string;
  direction: string;
  wiki: {
    what: string;
    where_from: string;
    impact: string;
    reduce: string;
    sources: string[];
  };
  limits: { grade: number; limit_value: number }[];
};

const GRADE_LABEL: Record<number, string> = {
  0: "通用",
  1: "Ⅰ 类",
  2: "Ⅱ 类",
  3: "Ⅲ 类",
  4: "Ⅳ 类",
  5: "Ⅴ 类",
};

export default function IndicatorDetailPage() {
  const params = useParams<{ code: string }>();
  const [data, setData] = useState<Detail | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/indicators/${params.code}`)
      .then((r) => {
        if (!r.ok) setMissing(true);
        return r.json();
      })
      .then((d) => setData(d))
      .catch(() => setMissing(true));
  }, [params.code]);

  if (missing) return <p>未找到该指标。</p>;
  if (!data) return <p className="text-slate-400">加载中…</p>;

  return (
    <article className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-slate-800">
          {data.name}
          {data.unit && <span className="ml-2 text-sm font-normal text-slate-400">{data.unit}</span>}
        </h1>
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-semibold text-brand">这是什么</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">{data.wiki.what}</p>
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-semibold text-brand">从哪里来</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">{data.wiki.where_from}</p>
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-semibold text-brand">有什么影响</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">{data.wiki.impact}</p>
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-semibold text-brand">怎么办</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">{data.wiki.reduce}</p>
        </section>
      </div>

      {data.limits.length > 0 && (
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-semibold text-slate-800">GB 3838-2002 标准限值</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {data.limits.map((l) => (
              <div
                key={l.grade}
                className="rounded-lg px-3 py-2 text-xs text-white"
                style={{ background: GRADE_COLORS[l.grade] || "#64748b" }}
              >
                {GRADE_LABEL[l.grade]}：{l.limit_value} {data.unit}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="text-xs text-slate-400">
        出处：{data.wiki.sources?.join("；")}
      </section>
    </article>
  );
}

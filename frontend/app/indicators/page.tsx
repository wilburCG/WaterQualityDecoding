"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Indicator = { code: string; name: string; unit: string; direction: string };

export default function IndicatorsPage() {
  const [items, setItems] = useState<Indicator[]>([]);

  useEffect(() => {
    fetch("/api/v1/indicators")
      .then((r) => r.json())
      .then(setItems);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800">水质指标百科</h1>
      <p className="mt-1 text-sm text-slate-500">
        每个指标是什么、从哪来、对人和水环境有什么影响、该怎么办。内容依据国家标准，
        点击查看详情与各类别限值。
      </p>
      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        {items.map((it) => (
          <Link
            key={it.code}
            href={`/indicators/${it.code}`}
            className="rounded-xl border border-slate-200 bg-white p-4 hover:border-brand/40"
          >
            <h3 className="font-semibold text-slate-800">
              {it.name}
              {it.unit && <span className="ml-2 text-xs font-normal text-slate-400">{it.unit}</span>}
            </h3>
            <p className="mt-1 text-xs text-slate-400">指标代码：{it.code}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

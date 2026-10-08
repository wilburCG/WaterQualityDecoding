"use client";

import { useRef, useState } from "react";
import { toPng } from "html-to-image";
import ReportView from "@/components/ReportView";
import { METHOD_LEVELS, type GradeResponse } from "@/lib/types";

const FIELDS = [
  { code: "ph", label: "pH（6~9 达标）", step: "0.01" },
  { code: "wt", label: "水温 ℃（参考）", step: "0.1" },
  { code: "do", label: "溶解氧 mg/L", step: "0.01" },
  { code: "codmn", label: "高锰酸盐指数 mg/L", step: "0.01" },
  { code: "nh3n", label: "氨氮 mg/L", step: "0.01" },
  { code: "tp", label: "总磷 mg/L", step: "0.01" },
  { code: "tn", label: "总氮 mg/L", step: "0.01" },
];

export default function DecodePage() {
  const [river, setRiver] = useState("");
  const [siteName, setSiteName] = useState("");
  const [sampledAt, setSampledAt] = useState("");
  const [methodLevel, setMethodLevel] = useState(1);
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<GradeResponse | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState<number | null>(null);
  const reportRef = useRef<HTMLDivElement>(null);

  const numericValues = () => {
    const out: Record<string, number> = {};
    for (const [k, v] of Object.entries(values)) {
      if (v.trim() !== "") out[k] = Number(v);
    }
    return out;
  };

  async function evaluate() {
    const res = await fetch("/api/v1/decode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ values: numericValues() }),
    });
    setResult(await res.json());
    setSaved(null);
  }

  async function saveShare() {
    if (!siteName.trim()) {
      alert("请先填写点位名称");
      return;
    }
    setSaving(true);
    try {
      const res = await fetch("/api/v1/samples", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          river,
          site_name: siteName,
          sampled_at: new Date(sampledAt || Date.now()).toISOString(),
          method_level: methodLevel,
          values: numericValues(),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || "保存失败");
        return;
      }
      setSaved(data.id);
    } finally {
      setSaving(false);
    }
  }

  async function downloadCard() {
    if (!reportRef.current) return;
    const dataUrl = await toPng(reportRef.current, { pixelRatio: 2, backgroundColor: "#ffffff" });
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = `水质体检报告-${siteName || "未命名"}.png`;
    a.click();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">报告解码</h1>
        <p className="mt-1 text-sm text-slate-500">
          把检测数值填进来（只填你测过的项目即可），系统依据 GB 3838-2002
          确定性规则评价，大模型不参与达标判定。
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="text-slate-600">河流名称</span>
            <input
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={river}
              onChange={(e) => setRiver(e.target.value)}
              placeholder="如：同汾泾"
            />
          </label>
          <label className="text-sm">
            <span className="text-slate-600">点位名称</span>
            <input
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={siteName}
              onChange={(e) => setSiteName(e.target.value)}
              placeholder="如：上游-浦三路桥"
            />
          </label>
          <label className="text-sm">
            <span className="text-slate-600">采样时间</span>
            <input
              type="datetime-local"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={sampledAt}
              onChange={(e) => setSampledAt(e.target.value)}
            />
          </label>
          <label className="text-sm">
            <span className="text-slate-600">检测方式（可信度）</span>
            <select
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={methodLevel}
              onChange={(e) => setMethodLevel(Number(e.target.value))}
            >
              {METHOD_LEVELS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {FIELDS.map((f) => (
            <label key={f.code} className="text-sm">
              <span className="text-slate-600">{f.label}</span>
              <input
                type="number"
                step={f.step}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={values[f.code] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [f.code]: e.target.value }))}
              />
            </label>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            onClick={evaluate}
            className="rounded-full bg-brand px-6 py-2.5 text-sm font-medium text-white"
          >
            生成水质体检报告
          </button>
          <button
            onClick={saveShare}
            disabled={saving}
            className="rounded-full border border-slate-300 px-6 py-2.5 text-sm text-slate-700 disabled:opacity-50"
          >
            {saving ? "保存中…" : "保存并分享"}
          </button>
        </div>
        {saved != null && (
          <p className="mt-3 text-xs text-green-600">
            已保存（分享编号 #{saved}）。M2 上线众包地图后将进入先审后发流程。
          </p>
        )}
      </div>

      {result && (
        <div className="space-y-3">
          <div className="flex justify-end">
            <button
              onClick={downloadCard}
              className="rounded-full border border-brand px-5 py-2 text-sm text-brand"
            >
              下载分享卡片 PNG
            </button>
          </div>
          <ReportView
            ref={reportRef}
            result={result}
            river={river}
            siteName={siteName}
            sampledAt={sampledAt}
          />
        </div>
      )}
    </div>
  );
}

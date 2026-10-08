"use client";

import { forwardRef } from "react";
import { GRADE_COLORS, type GradeResponse } from "@/lib/types";

type Props = {
  result: GradeResponse;
  river?: string;
  siteName?: string;
  sampledAt?: string;
};

const INDICATOR_HINTS: Record<string, string> = {
  ph: "达标区间 6 ~ 9",
  do: "越高越好",
  codmn: "越低越好",
  nh3n: "越低越好",
  tp: "越低越好",
  tn: "越低越好",
};

const ReportView = forwardRef<HTMLDivElement, Props>(function ReportView(
  { result, river, siteName, sampledAt },
  ref,
) {
  const grade = result.overall_grade;
  const color = grade ? GRADE_COLORS[grade] : "#94a3b8";

  return (
    <div ref={ref} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="px-6 py-5 text-white" style={{ background: color }}>
        <p className="text-xs opacity-90">水质体检报告</p>
        <div className="mt-1 flex flex-wrap items-baseline gap-x-3">
          <span className="text-4xl font-bold">{result.overall_label ?? "—"}</span>
          <span className="text-sm opacity-90">{result.grade_status}</span>
        </div>
        {(river || siteName || sampledAt) && (
          <p className="mt-2 text-xs opacity-90">
            {[river && `河流：${river}`, siteName && `点位：${siteName}`, sampledAt && `采样：${sampledAt}`]
              .filter(Boolean)
              .join("　")}
          </p>
        )}
      </div>

      <div className="px-6 py-4">
        <p className="text-sm text-slate-700">
          <strong>一句话结论：</strong>
          {result.summary}
        </p>
        {result.deciding_factors.length > 0 && (
          <p className="mt-1 text-xs text-slate-500">
            定类因子：{result.deciding_factors.join("、")}（该项决定了断面水质类别）
          </p>
        )}
        {result.boundary_non_compliant.length > 0 && (
          <p className="mt-1 text-xs font-medium text-red-600">
            ⚠️ {result.boundary_non_compliant.join("、")} 超出国标允许范围
          </p>
        )}
      </div>

      <div className="space-y-3 px-6 pb-6">
        {Object.values(result.items).map((it) => {
          const c = it.grade ? GRADE_COLORS[it.grade] : it.compliant ? "#16a34a" : "#dc2626";
          return (
            <div key={it.code} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <span className="font-medium text-slate-800">{it.name}</span>
                  <span className="ml-2 text-xs text-slate-400">
                    {INDICATOR_HINTS[it.code] || ""}
                  </span>
                </div>
                <span
                  className="rounded-md px-2 py-0.5 text-xs font-medium text-white"
                  style={{ background: c }}
                >
                  {it.grade_status ? it.grade_status.split("：")[0] : it.compliant ? "达标" : "超标"}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-700">
                实测值 <strong>{it.value}</strong> {it.unit}
                {it.limit_value != null && (
                  <span className="text-slate-500">
                    {" "}
                    · 对应限值 {it.limit_value} {it.unit}
                  </span>
                )}
                {it.exceed_ratio != null && (
                  <span className="text-red-600"> · 超出Ⅴ类限值约 {it.exceed_ratio.toFixed(2)} 倍</span>
                )}
              </p>
              {it.grade_status && it.grade && (
                <p className="mt-1 text-xs text-slate-500">{it.grade_status}</p>
              )}
            </div>
          );
        })}
      </div>

      <div className="border-t border-slate-100 px-6 py-3 text-center text-[11px] text-slate-400">
        水质解码器 WaterQualityDecoding · 依据 GB 3838-2002 评价 · 仅供科普参考
      </div>
    </div>
  );
});

export default ReportView;

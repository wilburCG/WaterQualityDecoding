"use client";

import { useRef, useState } from "react";

type ExtractResult = {
  file_type: string;
  values: Record<string, number>;
  site?: string;
  river?: string;
  date?: string;
  tip?: string;
  warning?: string;
};

const ACCEPT = ".xlsx,.xlsm,.csv,.pdf,.jpg,.jpeg,.png,.webp,.bmp";

const TYPE_LABELS: Record<string, string> = {
  excel: "Excel 表格",
  csv: "CSV 文件",
  pdf: "PDF 文档",
  image: "照片/截图",
};

export default function FileExtract({
  onResult,
}: {
  onResult: (r: ExtractResult) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "warn" | "err"; text: string } | null>(null);
  const [dragging, setDragging] = useState(false);

  async function handleFile(file: File) {
    setBusy(true);
    setMsg(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/v1/extract", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) {
        setMsg({ kind: "err", text: data.detail || "抽取失败" });
        return;
      }
      const count = Object.keys(data.values || {}).length;
      if (count) {
        setMsg({
          kind: "ok",
          text: `已从${TYPE_LABELS[data.file_type] || "文件"}识别出 ${count} 个指标，请核对后生成报告`,
        });
      } else {
        setMsg({ kind: "warn", text: data.warning || "未识别出指标数据" });
      }
      onResult(data as ExtractResult);
    } catch {
      setMsg({ kind: "err", text: "网络错误，请重试" });
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="text-sm font-semibold text-slate-800">📄 从文件 / 照片自动识别（M4）</h2>
      <p className="mt-1 text-xs leading-5 text-slate-500">
        支持 Excel、CSV、PDF 检测报告，或检测单/仪器屏幕的照片截图。识别结果自动填入下方表单，
        <b>请务必人工核对数值与单位</b>，确认无误后再生成报告。
      </p>

      <div
        onClick={() => !busy && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const f = e.dataTransfer.files?.[0];
          if (f && !busy) handleFile(f);
        }}
        className={`mt-4 cursor-pointer rounded-xl border-2 border-dashed px-6 py-7 text-center text-sm transition ${
          dragging ? "border-brand bg-brand-light text-brand" : "border-slate-300 text-slate-500 hover:border-brand hover:bg-brand-light"
        }`}
      >
        {busy ? "正在识别，请稍候…" : "点击选择文件，或把文件拖拽到这里"}
        <span className="mt-1 block text-[11px] text-slate-400">
          xlsx / csv / pdf / jpg / png，单个文件 ≤ 10MB
        </span>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleFile(f);
        }}
      />

      {msg && (
        <p
          className={`mt-3 rounded-lg px-3 py-2 text-xs ${
            msg.kind === "ok"
              ? "bg-green-50 text-green-700"
              : msg.kind === "warn"
                ? "bg-amber-50 text-amber-700"
                : "bg-red-50 text-red-700"
          }`}
        >
          {msg.text}
        </p>
      )}
    </div>
  );
}

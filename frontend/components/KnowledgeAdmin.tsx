"use client";

import { useEffect, useState } from "react";
import { apiFetch, useAuth } from "@/lib/auth";

type Doc = {
  id: number;
  title: string;
  source: string;
  source_url: string;
  category: string;
  is_published: boolean;
  chunk_count: number;
};

const CATEGORIES = [
  { value: "standard", label: "国家标准" },
  { value: "science", label: "水知识科普" },
  { value: "guide", label: "生活/净水指南" },
];

const EMPTY_FORM = {
  title: "",
  source: "",
  source_url: "",
  category: "science",
  content: "",
};

export default function KnowledgeAdmin() {
  const { token } = useAuth();
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    if (!token) return;
    const res = await apiFetch("/api/v1/admin/knowledge/docs", token);
    if (res.ok) setDocs(await res.json());
  }

  useEffect(() => {
    load();
  }, [token]);

  async function submit() {
    if (!form.title.trim() || !form.content.trim()) {
      setError("标题和正文不能为空");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const res = await apiFetch("/api/v1/admin/knowledge/docs", token, {
        method: "POST",
        body: JSON.stringify(form),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.detail || "保存失败");
        return;
      }
      setForm({ ...EMPTY_FORM });
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function togglePublish(d: Doc) {
    const res = await apiFetch(`/api/v1/admin/knowledge/docs/${d.id}`, token, {
      method: "PATCH",
      body: JSON.stringify({ is_published: !d.is_published }),
    });
    if (res.ok) await load();
  }

  async function remove(d: Doc) {
    if (!window.confirm(`确认删除《${d.title}》及其全部分块？`)) return;
    const res = await apiFetch(`/api/v1/admin/knowledge/docs/${d.id}`, token, {
      method: "DELETE",
    });
    if (res.ok) await load();
  }

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-800">新增知识文档</h2>
        <p className="mt-1 text-xs text-slate-400">
          入库后自动分块并生成向量；问答只会引用「已发布」的文档。请只收录权威、可溯源的内容。
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <input
            placeholder="文档标题"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-sky-400"
          />
          <input
            placeholder="来源（如：GB 3838-2002 / 生态环境部）"
            value={form.source}
            onChange={(e) => setForm({ ...form, source: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-sky-400"
          />
          <input
            placeholder="来源链接（可选）"
            value={form.source_url}
            onChange={(e) => setForm({ ...form, source_url: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-sky-400 sm:col-span-2"
          />
          <select
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-sky-400"
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <textarea
          placeholder="正文（段落之间空一行，便于自动分块）"
          rows={8}
          value={form.content}
          onChange={(e) => setForm({ ...form, content: e.target.value })}
          className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm leading-7 outline-none focus:border-sky-400"
        />
        {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
        <div className="mt-3">
          <button
            onClick={submit}
            disabled={saving}
            className="rounded-full bg-sky-600 px-5 py-2 text-xs font-medium text-white disabled:opacity-50"
          >
            {saving ? "正在分块嵌入…" : "保存并入库"}
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {docs === null ? (
          <p className="text-sm text-slate-400">加载中…</p>
        ) : docs.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-slate-300 bg-white px-8 py-10 text-center text-sm text-slate-500">
            暂无知识文档
          </p>
        ) : (
          docs.map((d) => (
            <div key={d.id} className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4">
              <div>
                <p className="text-sm font-medium text-slate-800">《{d.title}》</p>
                <p className="text-xs text-slate-400">
                  {CATEGORIES.find((c) => c.value === d.category)?.label}
                  {d.source ? ` · ${d.source}` : ""} · {d.chunk_count} 个分块
                </p>
              </div>
              <div className="ml-auto flex items-center gap-3 text-xs">
                <button onClick={() => togglePublish(d)} className={d.is_published ? "text-green-600" : "text-slate-400"}>
                  {d.is_published ? "✓ 已发布" : "已下线（点此发布）"}
                </button>
                <button onClick={() => remove(d)} className="text-red-500">
                  删除
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

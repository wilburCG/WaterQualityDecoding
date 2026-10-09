"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch, useAuth } from "@/lib/auth";

type Citation = {
  index: number;
  doc_id: number;
  doc_title: string;
  source: string;
  source_url: string;
  excerpt: string;
  score: number;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  suggestions?: string[] | null;
};

const CLIENT_KEY = "wqd_client_id";
const HISTORY_KEY = "wqd_ask_history";

const EXAMPLE_QUESTIONS = [
  "水质的Ⅰ-Ⅴ类是怎么划分的？",
  "溶解氧低说明什么？",
  "河水发绿、有异味是什么原因？",
  "家里自来水烧开有水垢正常吗？",
];

function getClientId() {
  let id = localStorage.getItem(CLIENT_KEY);
  if (!id) {
    id = "c-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem(CLIENT_KEY, id);
  }
  return id;
}

/** 把正文中的 [n] 引用标记渲染为角标。 */
function renderWithCitations(text: string) {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/);
    if (m) {
      return (
        <sup key={i} className="ml-0.5 rounded bg-sky-100 px-1 text-[10px] font-semibold text-sky-700">
          {m[1]}
        </sup>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export default function AskPage() {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [quota, setQuota] = useState<{ used: number; limit: number } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (raw) {
      try {
        setMessages(JSON.parse(raw));
      } catch {
        /* ignore */
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-50)));
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || loading) return;
    setInput("");
    setLoading(true);
    const userMsg: Message = {
      id: "u" + Date.now(),
      role: "user",
      content: q,
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await apiFetch("/api/v1/ask", token, {
        method: "POST",
        body: JSON.stringify({ question: q, client_id: getClientId() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "提问失败");
      setQuota(data.quota);
      setMessages((prev) => [
        ...prev,
        {
          id: "a" + Date.now(),
          role: "assistant",
          content: data.answer,
          citations: data.citations,
          suggestions: data.suggested_questions,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: "e" + Date.now(),
          role: "assistant",
          content: `⚠️ ${err instanceof Error ? err.message : "请求失败，请稍后再试"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function clearHistory() {
    setMessages([]);
    localStorage.removeItem(HISTORY_KEY);
  }

  const empty = messages.length === 0;

  return (
    <div className="mx-auto flex h-[calc(100vh-120px)] max-w-3xl flex-col">
      <div className="flex items-end justify-between pb-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-800">🤖 水质知识问答</h1>
          <p className="text-xs text-slate-500">
            回答基于国家标准与审核过的科普资料，强制附出处；仅供科普参考，非医疗或安全结论。
          </p>
        </div>
        {!empty && (
          <button onClick={clearHistory} className="text-xs text-slate-400 hover:text-slate-600">
            清空对话
          </button>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4">
        {empty && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <p className="text-sm text-slate-500">想问点什么？可以从下面的问题开始：</p>
            <div className="mt-4 flex max-w-lg flex-wrap justify-center gap-2">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1.5 text-xs text-sky-700 transition hover:bg-sky-100"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={
                m.role === "user"
                  ? "max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-sky-600 px-4 py-2.5 text-sm leading-7 text-white"
                  : "max-w-[90%] rounded-2xl rounded-bl-sm bg-slate-50 px-4 py-3 text-sm leading-7 text-slate-700"
              }
            >
              <div className="whitespace-pre-wrap">{renderWithCitations(m.content)}</div>

              {m.suggestions && m.suggestions.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {m.suggestions.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 hover:bg-slate-100"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {m.citations && m.citations.length > 0 && (
                <div className="mt-3 space-y-2 border-t border-slate-200 pt-3">
                  <p className="text-[11px] font-medium text-slate-400">参考来源</p>
                  {m.citations.map((c) => (
                    <div key={c.index} className="rounded-lg bg-white px-3 py-2 text-xs leading-5 text-slate-500">
                      <span className="mr-1 inline-flex h-4 w-4 items-center justify-center rounded bg-sky-100 text-[10px] font-semibold text-sky-700">
                        {c.index}
                      </span>
                      <span className="font-medium text-slate-700">《{c.doc_title}》</span>
                      {c.source && <span className="text-slate-400"> · {c.source}</span>}
                      {c.source_url && (
                        <a
                          href={c.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="ml-1 text-sky-600 underline"
                        >
                          链接
                        </a>
                      )}
                      <p className="mt-1 line-clamp-2">{c.excerpt}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-sm bg-slate-50 px-4 py-3 text-sm text-slate-400">
              正在查找可靠资料…
            </div>
          </div>
        )}
      </div>

      <div className="pt-3">
        {quota && (
          <p className="pb-1 text-right text-[11px] text-slate-400">
            今日已用 {quota.used}/{quota.limit} 次
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入你的水质问题，例如：氨氮超标有什么危害？"
            maxLength={500}
            className="flex-1 rounded-full border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-100"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-full bg-sky-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            发送
          </button>
        </form>
      </div>
    </div>
  );
}

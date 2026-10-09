"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login, register } = useAuth();
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        if (!displayName.trim()) {
          setError("请填写昵称");
          return;
        }
        await register(email, password, displayName.trim());
      }
      router.push("/map");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="text-2xl font-bold text-slate-800">
        {mode === "login" ? "登录" : "注册"}
      </h1>
      <p className="mt-1 text-sm text-slate-500">
        登录后可把你的河流实测分享到众包地图，并管理自己的提交。
      </p>

      <form onSubmit={submit} className="mt-6 space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
        {mode === "register" && (
          <label className="block text-sm">
            <span className="text-slate-600">昵称</span>
            <input
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="在地图上展示的名字"
              maxLength={32}
            />
          </label>
        )}
        <label className="block text-sm">
          <span className="text-slate-600">邮箱</span>
          <input
            type="email"
            required
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </label>
        <label className="block text-sm">
          <span className="text-slate-600">密码</span>
            <input
              type="password"
              required
              minLength={6}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === "register" ? "至少 6 位" : ""}
            />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-full bg-brand px-6 py-2.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy ? "请稍候…" : mode === "login" ? "登录" : "注册并登录"}
        </button>

        <p className="text-center text-xs text-slate-500">
          {mode === "login" ? (
            <>
              还没有账号？
              <button type="button" className="text-brand" onClick={() => { setMode("register"); setError(""); }}>
                注册
              </button>
            </>
          ) : (
            <>
              已有账号？
              <button type="button" className="text-brand" onClick={() => { setMode("login"); setError(""); }}>
                去登录
              </button>
            </>
          )}
        </p>
      </form>

      <p className="mt-4 text-center text-xs text-slate-400">
        继续即表示同意众包数据为公民科学分享，<Link href="/" className="underline">仅供科普参考</Link>。
      </p>
    </div>
  );
}

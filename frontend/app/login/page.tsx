"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { phoneAuth, adminLogin } = useAuth();
  const router = useRouter();
  const [adminMode, setAdminMode] = useState(false);

  // 普通用户：名字 + 手机号
  const [displayName, setDisplayName] = useState("");
  const [phone, setPhone] = useState("");
  // 管理员
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (adminMode) {
        await adminLogin(email, password);
      } else {
        if (!displayName.trim()) {
          setError("请填写昵称");
          return;
        }
        await phoneAuth(phone.trim(), displayName.trim());
      }
      router.push(adminMode ? "/admin" : "/map");
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
        {adminMode ? "管理员登录" : "进入"}
      </h1>
      <p className="mt-1 text-sm text-slate-500">
        {adminMode
          ? "请使用管理员邮箱与密码。"
          : "填昵称和手机号即可，新手机号会自动注册；登录后可分享河流实测并管理提交。"}
      </p>

      <form onSubmit={submit} className="mt-6 space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
        {adminMode ? (
          <>
            <label className="block text-sm">
              <span className="text-slate-600">邮箱</span>
              <input
                type="email"
                required
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@wqd.local"
              />
            </label>
            <label className="block text-sm">
              <span className="text-slate-600">密码</span>
              <input
                type="password"
                required
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
          </>
        ) : (
          <>
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
            <label className="block text-sm">
              <span className="text-slate-600">手机号</span>
              <input
                type="tel"
                inputMode="numeric"
                required
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, "").slice(0, 11))}
                placeholder="11 位手机号"
              />
            </label>
          </>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-full bg-brand px-6 py-2.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy ? "请稍候…" : adminMode ? "登录" : "进入 / 注册"}
        </button>

        <p className="text-center text-xs text-slate-500">
          {adminMode ? (
            <button type="button" className="text-brand" onClick={() => { setAdminMode(false); setError(""); }}>
              ← 返回普通登录
            </button>
          ) : (
            <button type="button" className="text-slate-400" onClick={() => { setAdminMode(true); setError(""); }}>
              管理员使用密码登录
            </button>
          )}
        </p>
      </form>

      {!adminMode && (
        <p className="mt-4 text-center text-xs text-slate-400">
          继续即表示同意众包数据为公民科学分享，<Link href="/" className="underline">仅供科普参考</Link>。
        </p>
      )}
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "首页" },
  { href: "/decode", label: "报告解码" },
  { href: "/indicators", label: "指标百科" },
  { href: "/cases/tongfenjing", label: "案例：同汾泾" },
  { href: "/map", label: "河流地图" },
  { href: "/ask", label: "知识问答" },
];

export default function Nav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-1 overflow-x-auto px-4">
        <Link href="/" className="mr-3 flex shrink-0 items-center gap-2 font-bold text-brand">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-sm text-white">
            水
          </span>
          <span className="hidden sm:inline">水质解码器</span>
        </Link>
        {links.slice(1).map((l) => {
          const active = pathname === l.href;
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`shrink-0 rounded-full px-3 py-1.5 text-sm ${
                active ? "bg-brand-light text-brand" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {l.label}
            </Link>
          );
        })}
      </div>
    </header>
  );
}

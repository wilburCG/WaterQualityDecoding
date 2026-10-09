"use client";

import { useEffect, useRef } from "react";

export type SiteGroup = {
  key: string;
  name: string;
  river: string;
  lng: number;
  lat: number;
  latestGrade: number;
  samples: { id: number; sampledAt: string; grade: number | null }[];
};

const GRADE_HEX: Record<number, string> = {
  1: "#2563eb",
  2: "#0891b2",
  3: "#16a34a",
  4: "#ca8a04",
  5: "#ea580c",
  6: "#dc2626",
};

declare global {
  interface Window {
    AMap?: any;
    _wqdAmapReady?: () => void;
  }
}

export default function AmapView({ groups, focus }: {
  groups: SiteGroup[];
  focus: SiteGroup | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const key = process.env.NEXT_PUBLIC_AMAP_KEY;

  // 加载高德脚本
  useEffect(() => {
    if (!key || !containerRef.current || window.AMap) return;
    const script = document.createElement("script");
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${key}`;
    script.async = true;
    script.onload = () => {
      if (!window.AMap || !containerRef.current) return;
      const map = new window.AMap.Map(containerRef.current, {
        zoom: 13,
        mapStyle: "amap://styles/whitesmoke",
      });
      mapRef.current = map;
    };
    document.body.appendChild(script);
    return () => {
      // 页面卸载时保留脚本缓存即可
    };
  }, [key]);

  // 绘制标记
  useEffect(() => {
    const AMap = window.AMap;
    const map = mapRef.current;
    if (!AMap || !map) return;

    markersRef.current.forEach((m) => map.remove(m));
    markersRef.current = [];

    groups.forEach((g) => {
      const color = GRADE_HEX[g.latestGrade] ?? "#94a3b8";
      const marker = new AMap.CircleMarker({
        center: [g.lng, g.lat],
        radius: 9,
        strokeColor: "#ffffff",
        strokeWeight: 2,
        fillColor: color,
        fillOpacity: 0.9,
        cursor: "pointer",
      });
      const rows = g.samples
        .map((s) => {
          const label = s.grade === 6 ? "劣Ⅴ" : `${s.grade ?? "-"} 类`;
          return `${new Date(s.sampledAt).toLocaleDateString("zh-CN")}：${label}`;
        })
        .join("<br/>");
      marker.on("click", () => {
        new AMap.InfoWindow({
          content: `<div style="min-width:140px;padding:2px 4px">
            <b>${g.river ? g.river + " · " : ""}${g.name}</b><br/>
            <span style="color:#64748b;font-size:12px">${g.samples.length} 次分享</span><br/>
            <span style="font-size:12px">${rows}</span></div>`,
          offset: new AMap.Pixel(0, -8),
        }).open(map, [g.lng, g.lat]);
      });
      map.add(marker);
      markersRef.current.push(marker);
    });

    if (groups.length) {
      map.setFitView(markersRef.current, false, [40, 40, 40, 40]);
    }
  }, [groups, key]);

  // 侧边栏聚焦
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !focus) return;
    map.setZoomAndCenter(15, [focus.lng, focus.lat]);
  }, [focus]);

  if (!key) {
    return (
      <div className="flex h-full min-h-[320px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <p className="text-sm leading-7 text-slate-500">
          🗺️ 地图底图待接入<br />
          <span className="text-xs text-slate-400">
            高德 Web 端 JS API Key 配置后自动启用；下方已可浏览全部已审核的众包数据。
          </span>
        </p>
      </div>
    );
  }

  return <div ref={containerRef} className="h-full min-h-[420px] w-full rounded-2xl border border-slate-200" />;
}

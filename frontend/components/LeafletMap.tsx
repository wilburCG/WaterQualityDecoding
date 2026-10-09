"use client";

import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { wgs84ToGcj02 } from "@/lib/coord";

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

const GRADE_LABEL = ["", "Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "劣Ⅴ"];

/** WGS-84 点位转 GCJ-02（高德底图坐标）。 */
function toMapPoint(g: SiteGroup): L.LatLng {
  const [lng, lat] = wgs84ToGcj02(g.lng, g.lat);
  return L.latLng(lat, lng);
}

export default function LeafletMap({ groups, focus }: {
  groups: SiteGroup[];
  focus: SiteGroup | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);

  // 初始化地图（只一次）
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    // 初始中心也转成 GCJ-02
    const [cLng, cLat] = wgs84ToGcj02(121.52, 31.15);
    const map = L.map(containerRef.current, {
      zoomControl: true,
      attributionControl: true,
    }).setView([cLat, cLng], 13);

    // 高德矢量底图（无需 Key，国内直连；坐标 GCJ-02）
    const gaode = L.tileLayer(
      "https://webrd{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
      {
        subdomains: ["01", "02", "03", "04"],
        maxZoom: 18,
        attribution: "&copy; 高德地图",
      },
    );
    // 高德影像底图
    const satellite = L.tileLayer(
      "https://webst{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}",
      {
        subdomains: ["01", "02", "03", "04"],
        maxZoom: 18,
        attribution: "&copy; 高德地图",
      },
    );
    gaode.addTo(map);
    L.control.layers({ "高德地图": gaode, "高德卫星影像": satellite }).addTo(map);

    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    // 容器尺寸可能在挂载时未稳定
    setTimeout(() => map.invalidateSize(), 200);
  }, []);

  // 绘制点位
  useEffect(() => {
    const layer = layerRef.current;
    if (!layer) return;
    layer.clearLayers();

    groups.forEach((g) => {
      const color = GRADE_HEX[g.latestGrade] ?? "#94a3b8";
      const marker = L.circleMarker(toMapPoint(g), {
        radius: 9,
        color: "#ffffff",
        weight: 2,
        fillColor: color,
        fillOpacity: 0.9,
      });

      const rows = g.samples
        .map((s) => {
          const label = s.grade ? GRADE_LABEL[s.grade] : "-";
          return `${new Date(s.sampledAt).toLocaleDateString("zh-CN")}：${label} 类`;
        })
        .join("<br/>");

      marker.bindPopup(
        `<div style="min-width:150px">
           <b>${g.river ? g.river + " · " : ""}${g.name}</b><br/>
           <span style="color:#64748b;font-size:12px">${g.samples.length} 次分享</span><br/>
           <span style="font-size:12px;line-height:1.7">${rows}</span>
         </div>`,
      );
      layer.addLayer(marker);
    });

    const points = groups.map(toMapPoint);
    const map = mapRef.current!;
    if (points.length) {
      map.fitBounds(L.latLngBounds(points).pad(0.2));
    }
  }, [groups]);

  // 侧边栏聚焦
  useEffect(() => {
    if (!focus || !mapRef.current) return;
    const p = toMapPoint(focus);
    mapRef.current.flyTo(p, 15, { duration: 0.6 });
  }, [focus]);

  return (
    <div
      ref={containerRef}
      className="h-full min-h-[420px] w-full rounded-2xl border border-slate-200"
    />
  );
}

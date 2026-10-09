import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "水质解码器 WaterQualityDecoding",
  description:
    "上传检测数据，看懂家门口的河：水质报告解码、众包河流地图、免费水知识问答。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen text-slate-800">
        <AuthProvider>
          <Nav />
          <main className="mx-auto max-w-5xl px-4 pb-10 pt-8">{children}</main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}

import Link from "next/link";

const entries = [
  {
    href: "/decode",
    title: "报告解码",
    desc: "录入检测数据，自动对照国标生成看得懂的「水质体检报告」",
    badge: "可用",
    ready: true,
  },
  {
    href: "/map",
    title: "河流地图",
    desc: "在地图上查看与分享你家周边河流的实测水质",
    badge: "即将上线",
    ready: false,
  },
  {
    href: "/ask",
    title: "知识问答",
    desc: "免费向水质智能体提问，回答都有国标和文献出处",
    badge: "即将上线",
    ready: false,
  },
];

export default function Home() {
  return (
    <div>
      <section className="rounded-3xl bg-gradient-to-br from-brand to-brand-dark px-8 py-14 text-white">
        <p className="text-sm tracking-widest text-cyan-100">WaterQualityDecoding</p>
        <h1 className="mt-3 text-3xl font-bold leading-snug sm:text-4xl">
          上传一份检测数据，看懂家门口的河
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-cyan-50/90">
          水质解码器把专业的检测报告翻译成人人能懂的结论，汇集公众分享的河流实测结果，
          并提供有出处、可追溯的免费水知识问答。
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link
            href="/decode"
            className="rounded-full bg-white px-6 py-2.5 text-sm font-medium text-brand"
          >
            立即解码一份报告 →
          </Link>
          <Link
            href="/cases/tongfenjing"
            className="rounded-full border border-white/40 px-6 py-2.5 text-sm text-white"
          >
            看同汾泾案例
          </Link>
        </div>
      </section>

      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        {entries.map((e) => (
          <Link
            key={e.href}
            href={e.href}
            className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-brand/40 hover:shadow-sm"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-slate-800">{e.title}</h3>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] ${
                  e.ready ? "bg-brand-light text-brand" : "bg-slate-100 text-slate-500"
                }`}
              >
                {e.badge}
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-500">{e.desc}</p>
          </Link>
        ))}
      </section>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="font-semibold text-slate-800">公开案例 #1：同汾泾水质研究</h3>
        <p className="mt-2 text-sm leading-7 text-slate-600">
          上海浦东一条 2.07 公里的小河，上、中、下游三断面实测：上游 Ⅴ~劣Ⅴ
          类，流经 2 公里后下游稳定在 Ⅲ 类。案例讲清河水「夏季浑浊、发绿、发臭」的真实机理。
        </p>
        <Link href="/cases/tongfenjing" className="mt-3 inline-block text-sm font-medium text-brand">
          查看完整案例 →
        </Link>
      </section>
    </div>
  );
}

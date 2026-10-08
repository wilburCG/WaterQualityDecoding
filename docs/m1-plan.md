# M1 开发计划 — 报告解码最小闭环

> 项目：WaterQualityDecoding 水质解码器
> 制定：2026-10-08 by Mose
> 依据：docs/design-v0.2.md
> 执行人：Mose（独立开发）
> 工期：2–3 个工作日

## 0. 范围定义

**M1 交付一个可公开展示的闭环：手工录入检测数据 → 确定性国标评价 → 输出普通人看得懂的「水质体检报告」+ 指标百科 + 同汾泾案例。**

包含：
- 后端 API、规则引擎、数据库
- 前端：首页、录入解码页、体检报告页、指标百科页、案例页
- 种子数据：同汾泾 7 行实验室数据 + 指标/限值字典
- 单测：评价引擎 100% 回测报告数据

不包含（后续里程碑）：用户登录体系、众包地图（仅入口占位）、RAG 问答（仅入口占位）、OCR、后台审核界面（M2 时做，规则已定"先审后发"）。

## 1. 仓库结构

```
projects/water-quality-decoding/
├── docker-compose.yml            # postgres(PostGIS+pgvector) / backend / frontend
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml / requirements.txt
│   ├── alembic/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── db.py
│       ├── models/               # indicator, standard_limit, site, sample, measurement
│       ├── schemas/
│       ├── api/v1/               # decode, indicators, sites, samples
│       ├── core/
│       │   └── grading.py        # ★ 评价引擎（纯函数、无 I/O 依赖，便于单测）
│       └── seeds/                # 7 指标 + GB3838 限值 + 同汾泾数据
├── frontend/
│   ├── Dockerfile
│   └── (Next.js 14 App Router, Tailwind, shadcn/ui)
├── docs/
│   ├── design-v0.1.md
│   ├── design-v0.2.md
│   └── m1-plan.md（本文件）
└── assets/
    ├── river-report-2026-10-08.docx
    └── report.txt
```

## 2. 任务分解（按执行顺序）

### Day 1 — 地基与大脑

**T1 仓库骨架与基础设施（3h）**
- docker-compose：postgres:16-postgis（编译 pgvector）、backend(uvicorn)、frontend(next dev/start)
- backend FastAPI 骨架、健康检查、配置读取、CORS
- frontend create-next-app + Tailwind + shadcn/ui + 顶部导航
- 验收：三个容器起来，`/api/health` 200，首页可访问

**T2 评价引擎 grading.py（3h，核心）**
- 输入：`{indicator_code: value}`（任意指标子集）
- 规则：从 standard_limit 读限值；pH 单独判 6~9；DO 方向为 ≥，其余 ≤
- 输出：
  - 每个指标的 `grade`（Ⅰ/Ⅱ/Ⅲ/Ⅳ/Ⅴ/劣Ⅴ/达标外）
  - 断面综合类别 = 最差类别（一票否决）
  - `deciding_factors`（定类因子，可能多个）
  - 每项超标倍数、一句话标签
- 纯函数 + 限值以参数注入（方便以后加饮用水/地下水标准）
- 验收：`pytest tests/test_grading.py` 全绿（见 T3）

**T3 引擎回测单测（2h）**
- 用报告全部 7 行数据做表驱动测试：
  - 8/2：上游Ⅴ/TN、中游Ⅳ/TN、下游Ⅲ/无定类因子
  - 8/5：三林塘港Ⅴ/TN、上游劣Ⅴ/TN、中游Ⅲ、下游Ⅲ
- 边界用例：pH=6.0 与 9.0 边界、pH=5.9 判不达标、DO 2.0 恰为Ⅴ、空指标集、未知指标
- 验收：报告 7 行判定与原报告**逐行一致**，边界用例全覆盖

**T4 数据模型与迁移（2h）**
- 5 张表：indicator、standard_limit、site(PostGIS Point)、sample、measurement
- Alembic 首个迁移
- 验收：`alembic upgrade head` 成功，空间索引可用

### Day 2 — 数据与 API

**T5 种子数据脚本（2h）**
- 7 指标字典（code/名称/单位/方向/百科摘要）
- GB 3838-2002 河流限值（design-v0.2 §三 限值表）
- 同汾泾：点位 4 个（含三林塘港）、2 次采样、7 个 sample、测量值
- 验收：一条命令完成播种，DB 数据与报告一致

**T6 后端 API（3h）**
- `POST /api/v1/decode`：提交临时指标值 → 不入库直接返回评价结果（录入页实时预览用）
- `POST /api/v1/samples`：保存分享（M1 直接保存，M2 加审核字段与流程）
- `GET /api/v1/indicators` / `/{code}`：百科
- `GET /api/v1/cases/tongfenjing`：案例聚合数据（点位/采样/测量值/结论段）
- 验收：curl 走完四个接口，decode 结果与引擎单测一致

**T7 通俗解读文案库（2h）**
- 每指标 × 每个判定档的通俗文案（YAML/DB）：
  「这是什么」「你的水处于什么水平」「可能哪来的」「对人和水环境的影响」「怎么办」
- 综合类别一句话模板（Ⅲ 类："适合一般鱼类洄游和游泳区，作为景观水是健康的"等）
- 验收：7 指标 × 6 档无空缺，文案经 Wilbur 抽检

### Day 3 — 前端页面

**T8 录入与解码页 `/decode`（4h）**
- 表单：河流名、点位名、采样时间、检测方式可信度（4 档下拉）、7 指标数值（可只填部分）
- 提交后实时调 decode 接口 → 渲染「水质体检报告」
- 组件：综合类别大徽章（色：Ⅰ蓝/Ⅱ青/Ⅲ绿/Ⅳ黄/Ⅴ橙/劣Ⅴ红）、定类因子角标、逐项卡片（数值 vs 限值、进度条、通俗文案）、一句话总结
- 移动端可用（志愿者多用手机）
- 验收：录入报告任一行数据，页面判定与报告一致

**T9 分享卡片导出（1.5h）**
- html-to-image 生成竖版卡片：类别、河流、时间、关键三项、定类因子、二维码/水印"水质解码器"
- 验收：下载 PNG，飞书/朋友圈可直接发

**T10 指标百科页 `/indicators`（2h）**
- 列表 + 详情：定义、国标限值表（Ⅰ-Ⅴ 着色条）、来源、影响、怎么减少；文末引用
- 验收：7 篇完整，无空白

**T11 案例页 `/cases/tongfenjing`（2h）**
- 同汾泾故事线：河流简介（隐去作者全名：胡同学、程同学）→ 怎么采样 → 数据表格（两次采样）→ 三个机理图文卡：
  ① 夜间热分层混合 → 浑浊
  ② 氮磷富营养 → 藻类发绿 → 死藻腐烂发臭
  ③ 2km 自净：劣Ⅴ → Ⅲ
- 数据小交互：点位切换看类别
- 图片：从 docx 抽取现场/模型照片（仅用无学生正脸或可识别信息的）
- 验收：页面完整、无学校班级信息、无学生全名

**T12 首页 `/`（1.5h）**
- Hero："上传一份检测数据，看懂家门口的河" + 三入口
  （解码可用 / 地图"即将上线" / 提问"即将上线"）
- 同汾泾案例卡 + 免责声明
- 验收：Lighthouse 无硬伤，移动端正常

**T13 收尾（1.5h）**
- README（本地启动/播种/测试）、`.env.example`
- 全站页脚免责声明："公民科学分享，仅供科普参考，非官方监测结论"
- 全栈冒烟：清空 DB → 迁移 → 播种 → 页面走查
- 验收：新机器按 README 30 分钟内跑起完整 M1

## 3. 汇总

| 类别 | 数量 |
|---|---|
| 任务 | 13 项（T1–T13） |
| 预估工时 | 约 27.5h（2–3 个工作日） |
| 后端测试 | pytest：引擎回测 7 行 + 边界 ≥10 用例 |
| 前端页面 | 4 个（首页/解码/百科/案例） |

## 4. 风险与对策

1. **限值口径出错**（湖库 TP 限值与河流不同）→ M1 只支持河流类型，限值表带 water_body_type 字段，湖库置灰提示
2. **通俗文案的科学性** → 全部基于国标与报告参考文献，T7 留 Wilbur 抽检环节
3. **未成年人信息泄露** → 案例文案统一用"胡同学/程同学"，图片人工筛除可识别画面，T11 验收项
4. **前端生产构建坑**（FlexWorker 踩过：env 烧进 build）→ 前端走服务端代理调 backend，不在浏览器直连内部地址

## 5. M1 完成定义（DoD）

- [ ] 引擎 7 行回测 + 边界单测全绿
- [ ] 清空库重建+播种一键完成
- [ ] 录入同汾泾任一行数据，体检报告与原报告判定一致
- [ ] 百科 7 篇、案例页完整且合规
- [ ] README 可让他人独立部署

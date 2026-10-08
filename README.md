# WaterQualityDecoding 水质解码器

看懂家门口每一条河：把水质检测数据解码为人人能懂的「水质体检报告」，汇集公众的河流实测分享，并提供有出处的免费水知识问答。

- **报告解码**：录入检测数值 → 依据《地表水环境质量标准》GB 3838-2002 确定性规则评价 → 输出综合类别、定类因子与逐项通俗解读，可下载分享卡片。
- **众包河流地图**（M2）：公众按点位分享实测结果，数据先审后发、按检测方式可信度分级。
- **知识智能体**（M3）：RAG 问答，回答强制附出处。

> ⚠️ 本站众包数据由公众自主分享，**仅供科普参考，非官方监测结论**。

## 技术栈

- 后端：FastAPI · SQLAlchemy 2 · Alembic · Python 3.11
- 数据库：PostgreSQL 16 + PostGIS（M3 起使用 pgvector）
- 前端：Next.js 14（App Router）· TailwindCSS · TypeScript
- 部署：Docker Compose

## 本地启动

```bash
cp .env.example .env
docker compose up -d --build
```

- 前端：http://localhost:3003
- 后端：http://localhost:8003（健康检查 /api/health）

初始化数据库与种子数据（同汾泾案例）：

```bash
docker compose exec wqd-backend alembic upgrade head
docker compose exec wqd-backend python -m app.seeds.seed
```

## 测试

```bash
cd backend
python3.11 -m pytest -v
```

评价引擎为纯确定性逻辑，单测以同汾泾报告全部 7 行数据回测，类别与定类因子与原报告逐行一致。

## 里程碑

| 阶段 | 内容 | 状态 |
|---|---|---|
| M1 | 评价引擎 · 手工录入 · 水质体检报告 · 指标百科 · 同汾泾案例 | ✅ |
| M2 | 用户体系 · 众包地图 · 先审后发后台 | ⏳ |
| M3 | RAG 知识智能体 · 引用溯源 · 免费开放 | ⏳ |
| M4 | PDF / 照片 OCR 自动抽取 | ⏳ |
| M5 | 官方监测数据对照 · 订阅提醒 | ⏳ |

## 合规

- 涉及未成年人的案例一律隐名，不出现学校、班级信息。
- 众包数据显著标注"公民科学分享，非官方结论"。

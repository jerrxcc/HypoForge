# HypoForge

HypoForge 是一个面向科研选题的 hypothesis workbench。输入一个研究主题后，它会从学术检索开始，逐步生成可追溯的 evidence cards、conflict clusters、3 条排序后的 hypotheses，以及一份 Markdown research briefing。

当前仓库已经不是早期的后端原型，而是一个以 `FastAPI + OpenAI Responses + SQLAlchemy` 为核心、配套 `frontend-v2` 仪表盘的全栈项目。

## 当前状态

截至 `2026-03-17`，基于仓库代码、提交历史和本地验证，可以确认的状态是：

- 最新一轮有文档记录的真实链路验证是 `2026-03-10`
  - `docs/reports/2026-03-10-strict-8-topic-live-report.md`
  - 严格 grounding 模式下完成 `8/8` 个真实 topic 的端到端 run
  - frontend 的 overview / trace / report 路由全部返回 `200`
- 代码在这之后继续推进了几项重要能力
  - `2026-03-11`: reflection-correction loop
  - `2026-03-13`: `frontend-v2` 新仪表盘
  - `2026-03-15`: validation agents
  - `2026-03-17`: live regression termination hardening 与 frontend markdown 依赖修复
- 我刚在本地重新验证了当前仓库
  - `./.venv/bin/pytest -q` -> `175 passed, 6 skipped`
  - `cd frontend-v2 && npm run build` -> pass
  - `cd frontend-v2 && npm run lint` -> fail
    - 当前为 `1` 个 ESLint error 和 `6` 个 warnings，前端还不是完全 CI-clean 状态

结论应当表述为：

- HypoForge 的后端主流程、存储层、trace 记录、报告渲染和 `frontend-v2` 核心页面都已经落地
- 最新“有报告支撑”的 live 批量验证仍然停留在 `2026-03-10`
- reflection / validation agents 已经在代码和测试中实现，但还没有对应的新 live report 写入 `docs/reports/`

## 它能做什么

给定一个研究主题，HypoForge 当前会执行一条四阶段主流程：

1. `retrieval`
   - 调 OpenAlex 和 Semantic Scholar 搜索论文
   - 去重、排序并保存 selected papers
   - 低召回时自动扩展检索窗口，并在必要时从候选池补足选择集
2. `review`
   - 分批读取 selected papers
   - 抽取结构化 evidence cards
   - 某些 batch 失败时保留 partial extraction
3. `critic`
   - 聚合 supporting / conflicting evidence
   - 形成 conflict clusters 与 divergence explanation
4. `planner`
   - 生成严格限定的 `3` 条 hypotheses
   - 每条 hypothesis 都包含 support、counterevidence、prediction 和 minimal experiment
   - 输出最终 Markdown briefing

每次 run 最终可以保存并返回：

- `selected_papers`
- `evidence_cards`
- `conflict_clusters`
- `hypotheses`
- `report_markdown`
- `stage_summaries`
- `trace`

## 关键能力

### 1. Research Briefing 输出

最终报告不再只是简单计数，而是一份带结构的 research briefing，当前包含：

- Executive Summary
- Retrieval Coverage
- Evidence Footing
- Conflict Map Snapshot
- 3 条 Ranked Hypotheses
- Experiment Slate
- Evidence Appendix
- Paper Appendix

### 2. Degraded / Partial Result 设计

HypoForge 不是 all-or-nothing 流水线。当前实现支持：

- stage summary 记录 `started` / `completed` / `degraded` / `failed`
- review / critic / planner 在部分失败时保留可用产物
- planner 失败后保留 partial report
- 当前置证据已存在时，只重跑 planner

### 3. Reflection-Correction Loop

主流程外，代码已经支持可配置的 reflection 层：

- 各 stage 的质量阈值
- iteration state 持久化
- feedback 历史记录
- 跨 stage backtracking

### 4. Validation Agents

代码也已经支持 validation 层，用于在主流程后补充质量控制：

- evidence validation
- conflict validation / enrichment
- hypothesis quality assessment
- synthesized feedback 和 backtrack recommendation

这部分能力已经有测试覆盖，但 README 这里不把它描述成“已完成新一轮 live 批量验证”的能力，因为当前 `docs/reports/` 还没有对应报告。

## 产品表面

### Backend API

当前公开的 HTTP 接口如下：

- `GET /healthz`
  - 健康检查
- `GET /v1/runs`
  - 列出 run archive
- `POST /v1/runs`
  - 同步执行完整 pipeline，直接返回最终结果
- `POST /v1/runs/launch`
  - 异步创建 run，并由 FastAPI background task 执行
- `GET /v1/runs/{run_id}`
  - 读取完整 dossier
- `GET /v1/runs/{run_id}/trace`
  - 读取工具调用 trace
- `GET /v1/runs/{run_id}/report.md`
  - 读取 Markdown briefing
- `POST /v1/runs/{run_id}/planner/rerun`
  - 在已有证据基础上只重跑 planner

### Frontend

当前活跃前端是 `frontend-v2/`，不是旧的 `frontend/`。

`frontend-v2` 当前提供这些页面：

- `/dashboard`
  - dashboard 首页，展示总 run 数、聚合统计、golden topics 和 recent runs
- `/dashboard/new`
  - 新建 run，支持 topic 输入和高级 constraints
- `/dashboard/runs`
  - run archive 浏览页
- `/dashboard/runs/[id]`
  - 单次 run 的 overview，含 status、stage progress、papers、evidence、conflicts、hypotheses
- `/dashboard/runs/[id]/trace`
  - tool trace inspector
- `/dashboard/runs/[id]/report`
  - Markdown briefing 查看与下载

当前前端能力更适合描述为“内部可用 dashboard / working console”，而不是完全生产就绪的产品界面。

## 技术栈

### Backend

- Python `3.12`
- FastAPI
- OpenAI Responses API
- Pydantic v2
- SQLAlchemy
- SQLite 默认存储

### Frontend

- Next.js `16`
- React `19`
- TypeScript
- TanStack Query
- Radix UI primitives
- Tailwind CSS `4`

### Scholarly Connectors

- OpenAlex
- Semantic Scholar

## 项目结构

```text
.
├── src/hypoforge/
│   ├── api/                 # FastAPI app, routes, public schemas
│   ├── application/         # coordinator, service wiring, report renderer
│   ├── agents/              # retrieval / review / critic / planner + reflection / validation
│   ├── domain/              # domain schemas, validation, quality logic
│   ├── infrastructure/      # DB models/repository, connectors, cache
│   └── tools/               # tool schemas and tool implementations
├── frontend-v2/             # 当前前端仪表盘
├── frontend/                # 旧前端，保留作参考
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── live/
├── docs/plans/              # 设计与实施计划
├── docs/reports/            # live verification 报告
└── scripts/run_topic.py     # CLI 入口
```

## 快速开始

### 1. 安装后端依赖

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -e '.[dev]'
```

### 2. 配置后端环境变量

可以从 `.env.example` 开始。最小可用配置如下：

```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=sqlite:///./hypoforge.db
FRONTEND_ALLOWED_ORIGINS=["http://127.0.0.1:3000"]
```

如果你只是想跑一个不依赖外部 API 的本地 smoke path，可以直接使用下面的 fake CLI 路径，不必先配 `OPENAI_API_KEY`。

### 3. 启动后端

```bash
./.venv/bin/uvicorn hypoforge.api.app:create_app --factory --reload
```

默认地址：

- API: `http://127.0.0.1:8000`
- Health: `http://127.0.0.1:8000/healthz`

### 4. 安装并启动前端

```bash
cd frontend-v2
npm install
npm run dev
```

前端默认地址：

- App: `http://127.0.0.1:3000`

前端使用的环境变量：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### 5. 从 UI 发起一次 run

1. 打开 `http://127.0.0.1:3000/dashboard`
2. 进入 `New Run`
3. 输入 topic 或选择 golden topic
4. 提交后跳转到 run detail 页面
5. 观察 stage 进度、dossier tabs、trace 和最终 report

## CLI 运行

### Fake 模式

不依赖 OpenAI / OpenAlex / Semantic Scholar，适合本地 smoke test：

```bash
./.venv/bin/python scripts/run_topic.py "solid-state battery electrolyte" --fake
```

### 真实模式

需要真实 API key：

```bash
./.venv/bin/python scripts/run_topic.py "solid-state battery electrolyte"
```

## 配置说明

### 常用后端配置

`.env.example` 中已经列出了完整字段。常用项包括：

- 应用与网络
  - `APP_ENV`
  - `APP_HOST`
  - `APP_PORT`
  - `LOG_LEVEL`
  - `FRONTEND_ALLOWED_ORIGINS`
- OpenAI
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `OPENAI_MODEL_RETRIEVAL`
  - `OPENAI_MODEL_REVIEW`
  - `OPENAI_MODEL_CRITIC`
  - `OPENAI_MODEL_PLANNER`
- 学术检索
  - `OPENALEX_API_KEY`
  - `SEMANTIC_SCHOLAR_API_KEY`
- 存储与缓存
  - `DATABASE_URL`
  - `RAW_RESPONSE_CACHE_TTL_SECONDS`
  - `NORMALIZED_PAPER_CACHE_TTL_SECONDS`
  - `EVIDENCE_CACHE_TTL_SECONDS`
- Pipeline 限制
  - `MAX_SELECTED_PAPERS`
  - `REVIEW_BATCH_SIZE`
  - `MAX_TOOL_STEPS_RETRIEVAL`
  - `MAX_TOOL_STEPS_REVIEW`
  - `MAX_TOOL_STEPS_CRITIC`
  - `MAX_TOOL_STEPS_PLANNER`
  - `MAX_OPENALEX_CALLS_PER_RUN`
  - `MAX_S2_CALLS_PER_RUN`
  - `REQUEST_TIMEOUT_SECONDS`

### Reflection 配置

reflection 相关配置使用 `REFLECTION_` 前缀，例如：

- `REFLECTION_ENABLE_REFLECTION`
- `REFLECTION_MAX_STAGE_ITERATIONS`
- `REFLECTION_MAX_CROSS_STAGE_ITERATIONS`
- `REFLECTION_RETRIEVAL_QUALITY_THRESHOLD`
- `REFLECTION_REVIEW_QUALITY_THRESHOLD`
- `REFLECTION_CRITIC_QUALITY_THRESHOLD`
- `REFLECTION_PLANNER_QUALITY_THRESHOLD`

### Validation 配置

validation 相关配置使用 `VALIDATION_` 前缀，例如：

- `VALIDATION_ENABLE_VALIDATION_AGENTS`
- `VALIDATION_MAX_BACKTRACK_PER_STAGE`
- `VALIDATION_MAX_TOTAL_BACKTRACK`
- `VALIDATION_BACKTRACK_DEPTH`
- `VALIDATION_MIN_VALID_EVIDENCE`
- `VALIDATION_MIN_CONFLICT_COVERAGE`
- `VALIDATION_MIN_QUALITY_SCORE`

## 测试

### 默认测试

```bash
./.venv/bin/pytest -q
```

当前本地结果：

- `175 passed, 6 skipped`

### live tests

真实外部依赖测试默认不跑，需要显式打开：

```bash
RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v
```

golden topic 回归还需要：

```bash
RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -v
```

### 当前测试覆盖的大方向

- API 路由
- run persistence / reconstruction
- stage summaries
- tool trace recording
- degraded / partial result 行为
- planner rerun
- reflection integration
- validation pipeline
- report renderer
- scholarly connectors 与 cache

## 最近的验证证据

如果你需要查看项目最近一次有明确记录的真实验证，建议从下面两个文件开始：

- `docs/reports/2026-03-10-strict-8-topic-live-report.md`
- `docs/reports/2026-03-10-multi-topic-live-report.md`

其中最强的一条当前可引用结论是：

- `2026-03-10` 的 strict run batch 在 `8` 个真实 topic 上取得 `8/8` 成功

## 限制与边界

当前 README 需要把边界说清楚：

- 当前主要基于论文 metadata / abstract 进行 synthesis，不是 full-text ingestion 系统
- 没有 auth、project、workspace、multi-user API
- planner 固定输出 `3` 条 hypotheses，这是刻意的产品约束
- `frontend-v2` 目前可 build，但 lint 还未完全清零
- validation agents 与 reflection 已在代码中实现，但新的 live batch 报告尚未补齐

## 开发建议

- 新增后端行为时，优先补 `tests/unit`，再补 `tests/integration`
- 影响 API 契约时，同时检查 `frontend-v2/src/types/api.ts`
- 修改报告结构时，同时检查
  - `src/hypoforge/application/report_renderer.py`
  - `frontend-v2/src/components/report/markdown-renderer.tsx`
- 需要真实验证时，优先复用 `tests/live/` 而不是手写一次性脚本

## 相关文档

- 设计 / 规划
  - `docs/plans/2026-03-08-hypoforge-design.md`
  - `docs/plans/2026-03-08-hypoforge-mvp.md`
  - `docs/plans/2026-03-10-hypoforge-briefing-depth-design.md`
- 验证报告
  - `docs/reports/2026-03-10-multi-topic-live-report.md`
  - `docs/reports/2026-03-10-strict-8-topic-live-report.md`

## License

MIT

# Task Plan: Build HypoForge From SPEC

## Goal
根据 `SPEC.md` 从零搭建 HypoForge MVP：完成 FastAPI + 多 agent 后端工程骨架、核心运行链路、测试与文档，并初始化 Git 仓库后同步到远程仓库。

## Current Phase
Phase 19 complete

## Phases
### Phase 1: Requirements & Discovery
- [x] 理解用户目标与约束
- [x] 检查项目当前状态与现有文件
- [x] 将关键发现记录到 `findings.md`
- [x] 明确远程仓库创建/同步策略
- **Status:** complete

### Phase 2: Design & Plan
- [x] 根据 SPEC 提炼 MVP 落地架构
- [x] 确认技术选型、目录结构、测试策略
- [x] 记录设计决策与分阶段实施计划
- **Status:** complete

### Phase 3: TDD Implementation
- [x] 先写失败测试，再实现 domain / tools / coordinator / API
- [x] 搭建配置、存储、renderer、trace 基础设施
- [x] 补齐 CLI / 文档 / 示例配置
- [x] 打通真实 OpenAI Responses API + 外部学术源 live run
- [x] 为真实运行路径补齐降级、schema 严格输出和候选池解析
- [x] 补齐真实运行路径的 trace 持久化与 `/trace` 内容验证
- **Status:** complete

### Phase 4: Git & Remote Sync
- [x] 初始化本地 Git 仓库
- [x] 配置 `.gitignore`、首次提交
- [x] 创建并推送远程仓库
- **Status:** complete

### Phase 5: Verification & Delivery
- [x] 运行测试与必要验证命令
- [x] 更新 `progress.md` 与最终状态
- [x] 向用户交付结果与后续说明
- [x] 对真实 live run 再做 fresh 验证
- [x] 对真实 `/trace` 与 API 结果做 fresh 验证
- [x] 等待并确认最新 fresh run 完成到 `done`
- **Status:** complete

### Phase 6: SPEC Hardening
- [x] 实现 raw response cache / normalized paper cache / evidence extraction cache
- [x] 补齐单源故障、critic/planner 失败时的降级返回
- [x] 扩充 trace 字段与阶段级日志，覆盖 tokens、request_id、stage summary
- [x] 为缓存/降级补齐单测与集成测试
- [x] 补齐 env-gated 的真实 API 端到端测试，并完成 fresh live 验证
- **Status:** complete

### Phase 7: Remaining SPEC Hardening
- [x] 将每阶段 summary 变成结构化持久化记录，并进入 API 结果
- [x] 将 review 改为按批次抽取，支持 partial extraction 和批次级降级
- [x] 为上述能力补齐 red-green tests，并重新执行 fresh verification
- **Status:** complete

### Phase 8: Retrieval Recovery Hardening
- [x] 实现 retrieval 结果过少时的一次自动放宽重试
- [x] 明确 low-evidence mode，并反映到结构化 stage summary
- [x] 为 retrieval recovery 与降级状态补齐 TDD 和 fresh verification
- **Status:** complete

### Phase 9: Structured Output Recovery
- [x] 为 structured output schema failure 增加一次自动重试
- [x] 为 retrieval/review/critic/planner 增加宿主侧 repair parse
- [x] 为上述恢复路径补齐 TDD 和 fresh verification
- **Status:** complete

### Phase 10: Planner Rerun Recovery
- [x] 实现 planner-only rerun 能力
- [x] 通过 API 暴露 planner rerun 路径
- [x] 为 rerun 路径补齐 TDD 和 fresh verification
- **Status:** complete

### Phase 11: External API Budget Enforcement
- [x] 实现 OpenAlex / Semantic Scholar 外部 API 调用次数上限
- [x] 仅在 cache miss 时扣减预算，并在超限时走降级而非中断
- [x] 为预算 enforcement 补齐 TDD 和 fresh verification
- **Status:** complete

### Phase 12: Hypothesis Credibility Hardening
- [x] 为 hypothesis 增加显式 limitations / uncertainty 承载字段
- [x] 在低证据 / critic 缺失 / review partial 时，由宿主侧自动补齐可信性说明
- [x] 为上述 hardening 补齐 TDD、报告渲染验证和 fresh verification
- **Status:** complete

### Phase 13: Tool Step Budget Closure
- [x] 将 `AgentRunner` 的 tool step 超限转为显式类型，而不是裸 `RuntimeError`
- [x] 对 retrieval/review/critic/planner 落地“超步数即返回已有最优结果”的阶段收束
- [x] 为 tool step budget 降级补齐 TDD 和 fresh verification
- **Status:** complete

### Phase 14: Golden Topics Regression
- [x] 为 5 个 golden topics 增加独立的 live regression suite
- [x] 抽取可复用的 live API helper，避免单 topic 和 golden suite 重复
- [x] 运行 golden regression 并更新文档/验证记录
- **Status:** complete

### Phase 15: Frontend Design
- [x] 基于 `frontend-design` 和 impeccable 指令型 skill 明确视觉方向与信息架构
- [x] 选择合适的开源前端框架/组件基底，避免重复造轮子
- [x] 输出设计方案并获用户确认后，再进入实现
- **Status:** complete

### Phase 16: Frontend Implementation
- [x] 按已确认方案引入 `Kiranism/next-shadcn-dashboard-starter` 到 `frontend/`
- [x] 先补 `GET /v1/runs` 与轻量 run list schema
- [x] 完成 `New Run`、`Runs`、`Run Detail / Overview`、`Trace`、`Report` 五个视图
- [x] 完成主题 token、字体、stage progress 与 trace inspector 的最小定制
- [x] 运行前后端联调与验证
- **Status:** in_progress

### Phase 17: Frontend Verification & Sync
- [x] 推送前端集成状态到远程
- [x] 执行 backend 全量、frontend build 与浏览器级 smoke
- [x] 修复 golden regression 暴露的 retrieval under-select 稳定性问题
- **Status:** complete

### Phase 18: Frontend Polish
- [x] 修复控制台布局的右侧空白与流体宽度问题
- [x] 收紧 `Runs / Overview / Trace / Report` 的展示密度与摘要层级
- [x] 将 run 详情头部改为真实 `topic` 驱动，而不是通用标题
- [x] 补前后端 red-green 测试，确保 `RunResult` 带回 `topic`
- [x] 完成 frontend lint/build 与 backend 全量验证
- [x] 新增异步 run launch，支持前端立即跳转到 live dossier 并轮询流程状态
- [x] 补运行中态的 loading skeleton、当前阶段强调和 trace/report live feedback
- [x] 为 `Runs` 页补 active run 快速入口、状态筛选和更明显的运行中徽章反馈
- [x] 为 `Overview / Trace` 补“刚更新/正在运行/最新 trace”这一层时间感提示
- [x] 为 `Runs / Overview / Trace` 统一微动效和 loading skeleton，完成最后一轮成品感收口
- [x] 完成一次真实 demo walkthrough：`New Run -> live run detail -> Trace -> Report -> Runs archive`
- [ ] 提交并推送本轮前端 polish
- **Status:** in_progress

### Phase 19: Report Depth & Retrieval Semantics
- [x] 按 SPEC 修正 retrieval 过度保守的 `degraded` 判定
- [x] 将最终报告升级为更高信息密度的 research briefing
- [x] 将 `Overview / Report` 前端改成 dossier 风格，突出 briefing 内容而不是只显示计数
- [x] 按 TDD 补齐报告结构和 retrieval 语义的红绿测试
- [x] 完成 backend / frontend fresh verification，并补记 planning files
- **Status:** complete

## Key Questions
1. 远程仓库是否默认创建到 GitHub，且是否使用私有仓库？
2. MVP 是否按 SPEC 落地为“真实 OpenAI/OpenAlex/S2 集成 + 本地 SQLite”，还是先保留可替换适配层并用测试桩保障可运行？

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 使用 `planning-with-files` 在项目根目录维护进度 | 任务跨度大，避免上下文丢失 |
| 先完成设计文档与实施计划，再进入实现 | 满足 `brainstorming` 与 `writing-plans` 的约束 |
| Git 初始化与远程同步纳入单独阶段 | 当前目录还不是 Git 仓库，且要在可运行状态后创建首个有意义提交 |
| 默认按 GitHub 私有仓库 `HypoForge` 同步远程 | 用户已确认继续按默认假设执行 |
| 真实外部依赖通过 adapter 保留，端到端验证默认使用 fake services | 既满足可测试性，又保留 OpenAI/OpenAlex/S2 接线点 |
| 真实链路调试继续遵循 `planning-with-files`，每轮修复后立即落盘 | 用户明确要求持续记录，避免上下文压缩丢失 |
| 前端采用 `Kiranism/next-shadcn-dashboard-starter` 作为壳子，并做最小必要调整 | 用户明确要求复用现成框架，不重复造轮子 |
| 前端主视图固定为 `New Run`、`Runs`、`Run Detail / Overview`、`Trace`、`Report` | 用户已经确认这一版信息架构 |
| 视觉方向固定为浅色“学术编辑台” | 用户明确要求默认浅色，且更适合研究人员 |
| 后端新增 `GET /v1/runs` 和轻量 run list schema | 为 `Runs` 页面提供真实历史数据 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `git status` 返回 `not a git repository` | 1 | 记录为当前初始状态，后续在 Phase 4 初始化仓库 |

## Notes
- 实现前需完成设计确认，并按 TDD 逐步落地。
- 远程同步需要明确托管平台/可见性，或确认采用默认假设。
- 每完成一个阶段都要同步更新本文件、`findings.md` 和 `progress.md`。
- GitHub CLI 已登录，可直接创建并推送私有仓库。
- 远程仓库已创建并推送到 `https://github.com/jerrxcc/HypoForge.git`。
- 当前在真实运行链路调试阶段，live run 正在执行；每次改动后都需要即时记录到 planning files。
- 2026-03-08 23:52 +08 已完成首次真实 live run 成功返回完整结果；下一步检查 trace 和 fresh 验证。
- 2026-03-08 23:55 +08 已确认 fresh run `run_6a638169c5c44fe28f02880d373d17ce` 至少推进到 `reviewing`，并已持久化 12 条 tool traces。
- 2026-03-09 00:00 +08 已确认 fresh verification 不能依赖 `ServiceContainer.repository`，后续统一使用 `coordinator` 或 `RunRepository` 查询 run/trace 状态。
- 2026-03-09 00:03 +08 已完成 fresh verification：全量 `pytest` 28 通过，最新真实 run `run_6a638169c5c44fe28f02880d373d17ce` 状态为 `done`，trace 共 19 条且覆盖 `retrieval/review/critic/planner` 四阶段，`GET /v1/runs/{id}`、`/trace`、`/report.md` 均返回 200。
- 2026-03-09 00:05 +08 已提交并推送真实链路修复 commit `67eb498 fix: harden live tool-calling workflow` 到 `origin/main`。
- 基于 SPEC 当前差距，推荐下一阶段优先做 `缓存 + 降级策略 + 可观测性补齐`；预算控制按用户要求暂缓。
- 2026-03-09 00:19 +08 Phase 6 新增测试已转绿，fresh 全量 `pytest` 为 `34 passed`；真实 live run 正在继续验证缓存/降级改动未破坏默认服务路径。
- 2026-03-09 00:22 +08 已确认最新真实 run `run_13693266052340eaab98cfe1ed69a82a` 当前推进到 `reviewing`，并已落 12 条 trace，trace 中可见 `request_id` / token 字段；但该 fresh live run 尚未完成到 `done`。
- 2026-03-09 00:27 +08 已确认同一 fresh run `run_13693266052340eaab98cfe1ed69a82a` 最终完成到 `done`，trace 共 19 条，说明 Phase 6 的缓存/降级改动未破坏真实默认链路。
- 2026-03-09 00:34 +08 已定位并修复真实 trace `input_tokens/output_tokens` 恒为 0 的根因：provider 在 tool-call turn 提前返回时丢失 `usage`；fresh run `run_07bb6d6f867a42db99fcec9c5e3b83bb` 已出现非零 token traces。
- 2026-03-09 00:39 +08 当前继续目标切换为“真实 API 测试完整跑通”：补一个 env-gated live integration test，覆盖 `POST /v1/runs` 与后续 `GET`/`/trace`/`/report.md` 读取路径，并在真实服务上执行。
- 2026-03-09 00:43 +08 真实 API live test 新暴露出跨 run 主键冲突：`evidence_cards.id` 直接使用模型输出的 `EV001`，导致第二次真实 run 失败；下一步修复 repository 的行级 ID namespacing，并重跑 live test。
- 2026-03-09 00:55 +08 已完成 repository 行级 ID namespacing 修复，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` 转绿，真实 `POST /v1/runs` 往返验证通过。
- 2026-03-09 01:00 +08 已完成带真实 API 的全量 fresh verification：`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` 结果为 `41 passed in 156.79s`，当前用户要求范围内的 SPEC hardening 已闭环。
- 2026-03-09 01:06 +08 用户同意继续按 SPEC 完善；当前进入 Phase 7，优先落结构化 `stage summary` 持久化和 review 分批抽取/partial extraction。
- 2026-03-09 01:14 +08 已完成第一轮实现：新增 `stage_summaries` 持久化、`RunResult.stage_summaries`、review batch helper、批次级 evidence append 和 partial failure 聚合；focused tests 当前 `10 passed`。
- 2026-03-09 01:24 +08 真实 live test 暴露 planner 在 `save_hypotheses` 处会因缺少 `counterevidence_ids` 降级失败；已在 workspace tool 边界加入基于 conflict clusters 的轻量修复。
- 2026-03-09 01:31 +08 fresh verification 已完成：`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` 为 `1 passed in 173.55s`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` 为 `45 passed in 186.22s`。
- 2026-03-09 01:39 +08 当前进入 Phase 8，按 SPEC 18.1 优先补 retrieval low-evidence recovery：结果过少时自动放宽一次检索窗口，仍不足则明确 low-evidence mode。
- 2026-03-09 01:44 +08 retrieval recovery 第一轮实现已完成：新增 `_run_retrieval_with_recovery()`，低召回时自动放宽 `year_from` 一次；`RetrievalSummary.coverage_assessment=low` 与 `ReviewSummary.failed_paper_ids` 现在会把对应 stage summary 标记为 `degraded`。focused tests 当前 `6 passed`。
- 2026-03-09 01:56 +08 fresh verification 已完成：`./.venv/bin/pytest -v` 为 `47 passed, 1 skipped`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` 为 `1 passed in 206.52s`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` 为 `48 passed in 236.87s`。
- 2026-03-09 02:03 +08 当前进入 Phase 9，按 SPEC 18.5 优先补 structured output recovery：先做一次自动重试，再做宿主侧 repair parse。
- 2026-03-09 02:08 +08 structured output recovery 第一轮实现已完成：`AgentRunner` 在 output model 校验失败时会先发一次 schema retry prompt，再走 repair callback；retrieval/review/critic/planner 已挂各自 repairer。focused tests 当前 `4 passed`。
- 2026-03-09 02:20 +08 fresh verification 已完成：`./.venv/bin/pytest -v` 为 `49 passed, 1 skipped`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` 为 `1 passed in 235.53s`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` 为 `50 passed in 228.74s`。
- 2026-03-09 02:27 +08 当前进入 Phase 10，按 SPEC 18.4 优先补 planner-only rerun。
- 2026-03-09 02:31 +08 planner rerun 第一轮实现已完成：新增 `RunCoordinator.rerun_planner()` 与 `POST /v1/runs/{run_id}/planner/rerun`。focused tests 当前 `6 passed`。
- 2026-03-09 02:44 +08 fresh verification 已完成：`./.venv/bin/pytest -v` 为 `51 passed, 1 skipped`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` 为 `1 passed in 452.52s`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` 为 `52 passed in 296.65s`。
- 2026-03-09 02:53 +08 当前进入 Phase 11，按 SPEC 第 16 节优先补外部 API 调用预算 enforcement。
- 2026-03-09 02:57 +08 外部 API budget 第一轮实现已完成：新增 `RunBudgetTracker` 和 `BudgetExceededError`，Cached connectors 只在 cache miss 时扣预算；超限时 scholarly tools 返回 `budget_exceeded`。focused tests 当前 `10 passed`。
- 2026-03-09 03:07 +08 在等待 Phase 11 的 fresh live verification 完成期间，继续对照 SPEC 第 18.3/19.2 节，进入 Phase 12：补 hypothesis 的 limitations / uncertainty 显式承载与宿主侧可信性修复。
- 2026-03-09 03:12 +08 Phase 12 第一轮实现已完成：`Hypothesis` 新增 `limitations` / `uncertainty_notes`，`save_hypotheses` 会按 retrieval/review/critic 的 degrade 状态自动补齐可信性说明，report renderer 也已同步展示。focused tests 当前 `3 passed`。
- 2026-03-09 03:21 +08 Phase 11/12 fresh verification 已完成：`./.venv/bin/pytest -v` 为 `56 passed, 1 skipped`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` 为 `1 passed in 215.29s`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` 为 `57 passed in 239.67s`。
- 2026-03-09 03:28 +08 当前进入 Phase 13，目标是补齐 SPEC 16.3 剩余的 `tool step budget` 收束逻辑，并据此更新整体完成度评估。
- 2026-03-09 03:34 +08 Phase 13 第一轮实现已完成：`AgentRunner` 现在抛 `ToolStepBudgetExceededError`，retrieval/review/critic/planner 都已接入阶段级收束；focused tests 当前 `8 passed`。
- 2026-03-09 03:43 +08 Phase 13 fresh verification 已完成：`./.venv/bin/pytest -v` 为 `59 passed, 1 skipped`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` 为 `1 passed in 179.16s`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` 为 `60 passed in 293.01s`。
- 2026-03-09 03:49 +08 当前进入 Phase 14，按 SPEC 22.2/24 的要求补 5 个 golden topics live regression。
- 2026-03-09 03:54 +08 Phase 14 第一轮实现已完成：新增 `hypoforge.testing.live_regressions` 共享 helper、参数化 golden suite，以及 README 中的 golden regression 跑法。focused tests 当前 `1 passed, 6 skipped`。
- 2026-03-09 11:05 +08 首次 golden regression 实跑结果为 `3 passed, 2 failed`；失败集中在 planner 入库边界，根因为真实模型未稳定提供 `>=3` 个 `supporting_evidence_ids`。
- 2026-03-09 11:29 +08 已完成 planner supporting-evidence repair，失败的两个 topic 先做 targeted rerun 后转绿：`2 passed, 3 deselected in 409.99s`。
- 2026-03-09 11:47 +08 5-topic golden regression fresh verification 已完成：`RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -v` 为 `5 passed in 1089.48s`。
- 2026-03-09 11:48 +08 默认全量测试已再次确认通过：`./.venv/bin/pytest -v` 为 `61 passed, 6 skipped`。
- 2026-03-09 13:43 +08 当前进入 Phase 15：按 `frontend-design` 与 impeccable 风格，为 HypoForge 设计首个 dashboard 型前端界面。
- 2026-03-09 14:12 +08 Phase 15 已完成：前端方案固定为复用 `Kiranism/next-shadcn-dashboard-starter`，保留 app shell/sidebar/shadcn primitives，替换默认首页、示例数据、导航结构和所有业务页面。
- 2026-03-09 14:12 +08 详情视图边界已固定：全局导航只保留 `New Run` / `Runs`，run 详情内部再切 `Overview` / `Trace` / `Report`。
- 2026-03-09 14:12 +08 当前进入 Phase 16：开始按 TDD 落地 `GET /v1/runs`、前端壳子和五个工作流视图。
- 2026-03-09 14:21 +08 Phase 16 第一轮 red-green 已完成：新增 `RunSummary` / `RunSummaryBody`、`GET /v1/runs`、`RunCoordinator.list_runs()` 和 `RunRepository.list_runs()`；同时补了可配置 CORS，使本地 `frontend` 可直接访问 FastAPI。
- 2026-03-09 14:21 +08 当前 focused backend verification 为 `./.venv/bin/pytest tests/integration/test_runs_api.py tests/integration/test_health_api.py -v`，结果 `6 passed`。
- 2026-03-09 14:43 +08 `frontend/` 已接入 starter 壳并去模板化：移除 auth/proxy 路由门禁，根路由与 `/dashboard` 都改为跳转到 `/dashboard/new-run`。
- 2026-03-09 14:43 +08 前端五个视图已落地：`New Run`、`Runs`、`Run Overview`、`Trace`、`Report`，并通过 `NEXT_PUBLIC_API_BASE_URL` 直连现有 FastAPI。
- 2026-03-09 14:43 +08 当前前端验证结果：`npx tsc --noEmit` 通过，`npm run lint` 通过，`npm run build` 通过。仅剩 `baseline-browser-mapping` 版本过旧提示，不阻断构建。
- 2026-03-09 14:49 +08 前后端本地联调 smoke 已完成：前端 `/` 正常 307 到 `/dashboard/new-run`，页面标题返回 `HypoForge Console`；后端 `GET /v1/runs` 返回真实 run 列表 JSON。
- 2026-03-09 14:49 +08 当前进入 Phase 17：推送前端集成状态到远程，并执行全流程 fresh verification，覆盖 backend 全量、真实 API、golden topics、frontend build 与浏览器级 smoke。
- 2026-03-09 15:27 +08 Phase 17 第一轮 full verification 已完成：`git push origin main` 已推送 `eda9ca9`；`./.venv/bin/pytest -v` 为 `65 passed, 6 skipped`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` 为 `1 passed in 219.60s`。
- 2026-03-09 15:45 +08 5-topic golden regression 首轮 fresh run 暴露真实稳定性问题：`diffusion model preference optimization` live run 一次性只选出 `<12` 篇 selected papers，未满足 SPEC 回归门槛。
- 2026-03-09 15:52 +08 已补 retrieval 宿主侧 candidate-pool backfill：broadened retrieval 后若模型 under-select，会按现有 ranking 从候选池补足到阈值；focused tests `4 passed`，失败 topic targeted rerun `1 passed, 4 deselected in 191.21s`。
- 2026-03-09 16:09 +08 golden regression 已重新 fresh 转绿：`RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -v` 为 `5 passed in 1010.48s`。
- 2026-03-09 16:24 +08 浏览器级 UI 审查暴露前端折叠态 overflow：sidebar 折叠时文本未隐藏、长 golden topic 按钮未换行、右侧 notes 存在断链。
- 2026-03-09 16:31 +08 已完成前端 overflow hardening：修正 sidebar `group-data` 选择器、补长文本换行和提交区窄屏堆叠、替换 infobar 断链；前端 `npm run lint` / `npm run build` 再次通过，并在 1024px / 768px 浏览器截图下确认不再出现明显越界。
- 2026-03-09 16:58 +08 已进一步处理“右侧大面积空白”问题：根因不是主内容不自适应，而是 dashboard layout 常驻了一个全局右侧 infobar，占用了固定 22rem 宽度。
- 2026-03-09 17:02 +08 已移除全局 infobar 占位，并把 `New Run` / `Run Overview` 的双栏布局触发点从 `xl` 推迟到 `2xl`；1440px 浏览器下页面现在由主内容吃满，不再保留右侧空白槽位。
- 2026-03-09 17:46 +08 当前进入 Phase 18：对前端控制台做一轮全面 polish，目标是统一 `Runs / Overview / Trace / Report` 的展示密度、语义摘要和响应式行为，并继续维持 planning files 及时回写。
- 2026-03-09 17:55 +08 Phase 18 第一轮实现已完成：新增 `hypoforge-display.ts` 摘要映射，重做 `Runs` 档案视图、`Run Overview`、`Trace` inspector、`Report` 侧栏和 `StageProgressBand`，同时把历史长错误信息压缩为 `compactError()` 预览。
- 2026-03-09 18:14 +08 已完成 Phase 18 的响应式收束：`Runs` 页表格展示推迟到 `xl`，1024px 改走卡片档案流；`StageProgressBand` 在中等桌面改为双列、仅在 `2xl` 回到四列，长文案不再被横向压扁。
- 2026-03-09 18:15 +08 fresh frontend verification 已完成：`cd frontend && npm run lint` 通过，`cd frontend && npm run build` 通过；Playwright 已复查 `Runs / Overview / Trace / Report` 在 1440px 和 1024px 下均无横向滚动，`Runs` 历史失败行也已稳定限制在卡片/徽章内。
- 2026-03-09 18:24 +08 用户反馈超宽屏下“整个卡片都没有填充完整屏幕”。已定位为 run 相关页面统一使用 `max-w-[1680px]` 的外层容器，导致在 2K 屏上被人为截断。
- 2026-03-09 18:28 +08 已移除 `New Run / Runs / Run Overview / Trace / Report` 五个视图外层的 `max-w-[1680px]` 限制；2048px 浏览器复查时，主内容轨道宽度为 `2000px`、首张主卡片宽度为 `1936px`，已接近可用主区域宽度。
- 2026-03-09 18:34 +08 用户继续反馈“现在变成超出屏幕显示范围”，说明不能简单去掉上限，必须用流体宽度。
- 2026-03-09 18:39 +08 已新增共享 `.workspace-shell` 容器：`width = min(100%, clamp(0px, calc(100vw - clamp(1.5rem, 3vw, 4.5rem)), 1980px))`，恢复自动居中，并接入五个工作区页面。
- 2026-03-09 18:40 +08 fresh frontend verification 已再次完成：`cd frontend && npm run lint` 通过，`cd frontend && npm run build` 通过；Playwright 在 `2048x1295` 下复查 `/dashboard/runs/{id}`，`content width = 1980px`、`first card = 1916px`、`scrollWidth == viewport`。
- 2026-03-09 18:47 +08 用户继续指出 `new-run` 页面仍然“超出屏幕显示范围”。已定位为 `.workspace-shell` 使用 `100vw` 参与计算，忽略了 sidebar 占位宽度，导致内容宽度大于父容器。
- 2026-03-09 18:50 +08 已将 `.workspace-shell` 修正为父容器驱动：`width: 100%; max-width: 1980px; margin-inline: auto;`。Playwright 复查 `/dashboard/new-run` 时，右侧 `Pipeline` 卡已完整回到主区域，`content width = 1980px`、`grid width = 1916px`、`scrollWidth == viewport`。
- 2026-03-09 19:08 +08 当前继续进行 Phase 18 细化 polish：开始把 run 详情页从“通用工作台标题”改成真实 topic 驱动，并进一步提升 `New Run / Trace / Report` 的研究语义摘要。
- 2026-03-09 19:11 +08 已按 TDD 先补 red test：`RunResult` 详情结果必须带回 `topic`，以支撑 dossier 头部展示真实研究主题；`tests/unit/test_repository.py` 与 `tests/integration/test_runs_api.py` 先红后绿。
- 2026-03-09 19:14 +08 本轮 polish 已完成代码层落地：`RunHero` 改为真实 topic 标题并补 papers/evidence/clusters/hypotheses 胶囊摘要，`New Run` 右栏新增 `Launch profile`，`Trace` 新增 cache-hit 摘要，`Report` 新增 uncertainty 摘要，sidebar 的 `Demo mode` 已替换为 `Live API`。
- 2026-03-09 19:17 +08 当前 fresh verification 已完成：`./.venv/bin/pytest -q` 为 `65 passed, 6 skipped`，`cd frontend && npm run lint` 通过，`cd frontend && npm run build` 通过。
- 2026-03-09 19:23 +08 已决定优先补齐“真实话题处理过程的流程可视化”，而不是继续做纯静态视觉 polish；实现策略为保留同步 `POST /v1/runs`，新增专供前端使用的异步 `POST /v1/runs/launch`。
- 2026-03-09 19:28 +08 异步 launch 已完成 red-green：后端新增 `launch_run/execute_run` 与 `/v1/runs/launch`，前端 `New Run` 改为点击后立即跳入 run 详情页，后续阶段和 trace 由现有 polling 持续刷新。
- 2026-03-09 19:30 +08 fresh verification 已再次完成：`./.venv/bin/pytest -q` 为 `66 passed, 6 skipped`，`cd frontend && npm run lint` 通过，`cd frontend && npm run build` 通过。
- 2026-03-09 19:37 +08 已继续打磨 live 运行体验：`Overview` 新增 live pipeline banner，`Trace` 新增 live feed banner 与空白 skeleton，`Report` 在 planner 未完成前新增 draft skeleton，占位不再塌陷。
- 2026-03-09 19:39 +08 本轮 fresh verification 已完成：`./.venv/bin/pytest -q` 为 `66 passed, 6 skipped`，`cd frontend && npm run lint` 通过，`cd frontend && npm run build` 通过。
- 2026-03-09 19:46 +08 已继续加强 archive 工作流：`Runs` 页新增 live docket 快速入口、`All/Active/Completed/Failed` 筛选，以及运行中 run 的更显著动态标记。
- 2026-03-09 19:47 +08 fresh verification 已完成：`./.venv/bin/pytest -q` 为 `66 passed, 6 skipped`，`cd frontend && npm run lint` 通过，`cd frontend && npm run build` 通过。
- 2026-03-09 19:55 +08 已继续做最后一层时间感 polish：`Overview` 的当前阶段卡片现在会强调“Receiving updates now / Updated x ago”，并默认展开当前或异常阶段的原始 payload；`Trace` 的最新条目会得到 `Latest` 标记和更强的 live 强调。
- 2026-03-09 19:56 +08 fresh verification 已完成：`./.venv/bin/pytest -q` 为 `66 passed, 6 skipped`，`cd frontend && npm run lint` 通过，`cd frontend && npm run build` 通过。
- 2026-03-09 20:03 +08 已完成最后一轮统一收口：`Runs` 新增 skeleton archive，`Overview` 的 stage cards 和 `Trace` 的条目改为轻量 stagger entrance，live 变化不再是纯静态跳变。
- 2026-03-09 20:04 +08 fresh verification 已完成：`./.venv/bin/pytest -q` 为 `66 passed, 6 skipped`，`cd frontend && npm run lint` 通过，`cd frontend && npm run build` 通过。
- 2026-03-09 20:14 +08 已完成真实 demo walkthrough 检查：通过 `/v1/runs/launch` 发起主题 `solid-state battery electrolyte`，run `run_506d493b908c4eb8bba6b120c7da55b1` 成功经历 `retrieving -> reviewing -> criticizing -> planning -> done` 全链路。
- 2026-03-09 20:14 +08 这次真实 walkthrough 的最终结果为：15 篇 selected papers、15 张 evidence cards、4 个 conflict clusters、3 个 hypotheses、4 条 stage summaries、18 条 traces；archive 命中，前端 `/dashboard/runs/{id}`、`/trace`、`/report` 路由均返回 200。
- 2026-03-10 13:33 +08 已完成多课题真实 live 验证：5 个真实研究课题通过 frontend+backend 链路发起异步 run，并验证 `/trace`、`/report.md`、`/v1/runs` 和前端 detail/trace/report 路由。
- 2026-03-10 13:33 +08 本轮结果为 4 个 `done`、1 个 `failed`；失败集中在 `diffusion model preference optimization` 的 planner hypothesis 校验，说明系统已“可跑通”，但仍缺一个 planner 低证据 fallback 收口。
- 2026-03-10 14:00 +08 已完成 planner 低证据 fallback 修复：当 supporting evidence 修复后仍不足 3 条时，宿主侧会做受控补位并添加 limitation，而不是让整条 run 在 `save_hypotheses` 校验处失败。
- 2026-03-10 14:00 +08 已完成失败课题 targeted live retest：`diffusion model preference optimization` fresh run `run_039a9802068c409898c963b574b53fc8` 按 `queued -> retrieving -> reviewing -> criticizing -> planning -> done` 成功完成，planner stage `completed`。
- 2026-03-10 14:25 +08 经对照 SPEC 原意，上一轮“重复 supporting evidence id 补位”的策略被判定为过于宽松，已撤回。
- 2026-03-10 14:25 +08 当前严格派实现为：`Hypothesis` 必须具备至少 3 个 distinct supporting evidence ids；若 planner 无法满足，则按既有 planner partial-result 路径失败/降级，而不伪装成成功。
- 2026-03-10 14:25 +08 fresh verification 已完成：`./.venv/bin/pytest -q` 为 `67 passed, 6 skipped`，`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` 为 `1 passed in 221.69s`。
- 2026-03-10 15:26 +08 已完成严格派 8-topic live 扩样：在完整 frontend+backend 链路上连续运行 8 个真实研究课题，结果 `8/8 done`，包括此前更敏感的 `diffusion model preference optimization`。
- 2026-03-10 15:26 +08 当前最强结论更新为：HypoForge 在 strict grounding 模式下，已经在 8-topic live batch 上完成端到端验证，且前端 detail/trace/report 路由全部返回 200。
- 2026-03-10 15:44 +08 已完成 OpenAlex API key 真接入：`Settings.openalex_api_key` 现在会传入 `OpenAlexConnector`，connector 在存在配置时会给 `/works` 请求附加 `api_key` query param。
- 2026-03-10 15:44 +08 本地 `.env` 已填入用户提供的 OpenAlex key；该值仅存在本地开发环境，不进入 git。
- 2026-03-10 15:44 +08 fresh verification 已完成：OpenAlex wiring focused tests `3 passed`，backend 全量 `69 passed, 6 skipped`，真实 round-trip `1 passed in 215.02s`。
- 2026-03-10 20:00 +08 已按用户要求将 GitHub 远程仓库 `jerrxcc/HypoForge` 的可见性从 `PRIVATE` 调整为 `PUBLIC`，并开始补记 planning files 与同步记录提交。
- 2026-03-10 20:17 +08 已启动 `CRISPR delivery lipid nanoparticles` 的 `degraded` 原因分析：目标是区分这是符合 SPEC 的保守降级，还是当前实现把 retrieval 标记得过于敏感。
- 2026-03-10 20:22 +08 用户已确认采用“方案 2”：主改后端产物深度、辅改前端 dossier 展示；这轮会同时修正 retrieval 的过度降级判定，并用 TDD 提升 run 完成后的信息量与说服力。
- 2026-03-10 20:36 +08 Phase 19 red tests 已建立：一条锁定 retrieval `medium + needs_broader_search` 不应自动 `degraded`，一条锁定 report 必须产出 `Executive Summary / Retrieval Coverage / Evidence Footing / Conflict Map / Appendix` 等 briefing sections。
- 2026-03-10 20:44 +08 Phase 19 backend green 已完成：`RunCoordinator._stage_status()` 对 retrieval 只在 `coverage_assessment == low` 时标记 `degraded`；`ReportRenderer` 已升级为多 section research briefing。
- 2026-03-10 20:49 +08 Phase 19 frontend dossier 改造已完成：`Run Overview` 新增 `Briefing focus`，`Report` 新增 `Coverage notes`、`Most cited evidence` 和更明确的阅读路径，前端不再主要依赖纯计数卡解释结果价值。
- 2026-03-10 21:00 +08 Phase 19 fresh verification 已完成：focused backend tests `9 passed`，backend 全量 `71 passed, 6 skipped`，真实 API round-trip `1 passed in 228.00s`，frontend `npm run lint` / `npm run build` 通过。真实 `CRISPR delivery lipid nanoparticles` run 的新 briefing 已抽样检查，内容密度显著高于旧版报告。

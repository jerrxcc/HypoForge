# Findings & Decisions

## Requirements
- 用户要求“使用 plan with file”，基于 [`SPEC.md`](/Users/ccy/Documents/KEY/HypoForge/SPEC.md) 进行整个项目搭建。
- 需要从空目录开始建立工程、Git 仓库，并同步远程。
- 需要优先遵循 SPEC 的 MVP 范围：FastAPI、Python 3.12、OpenAI Responses API / Agents SDK、OpenAlex、Semantic Scholar、SQLite、API-first。

## Research Findings
- 当前项目目录只有 `SPEC.md`，尚未存在代码、配置、测试或 Git 元数据。
- `SPEC.md` 明确给出四阶段固定流程：`retrieval -> review -> critic -> planner`。
- V1 采用 model-driven tool calling，应用层负责受控工具执行、预算、状态与 trace。
- 当前实现范围不包含浏览器自动化、PDF 解析、向量数据库、复杂前端、多租户。
- API 面包括 `POST /v1/runs`、`GET /v1/runs/{run_id}`、`GET /v1/runs/{run_id}/report.md`、`GET /v1/runs/{run_id}/trace`、`GET /healthz`。
- 数据层至少包含 `runs`、`papers`、`run_papers`、`evidence_cards`、`conflict_clusters`、`hypotheses`、`tool_traces`。
- `.env.example` 需暴露 OpenAI、OpenAlex、Semantic Scholar、SQLite、预算控制等配置项。
- 测试策略包含单元测试、集成测试和端到端测试，适合以 provider 抽象 + fake runtime 的方式先做可测试实现。
- 本机可用 `python3.12`，但默认 `python3` 是 3.9.6，因此项目验证统一使用 `./.venv/bin/python` 和 `./.venv/bin/pytest`。
- `gh auth status` 显示当前已登录 GitHub 账号 `jerrxcc`，具备 `repo` 等所需 scope，可直接创建私有仓库。
- 真实 OpenAI live run 调试中，已确认 Responses API function tool output 必须携带 `call_id`，且 `output` 需要是字符串；Structured Outputs 需要 `json_schema` 且 strict schema 必须包含 `additionalProperties: false` 和完整 `required`。
- 真实 retrieval 调试已经定位并修复了 4 个具体阻塞点：
- 1. `OPENAI_API_KEY` 没有从 settings 透传到 `OpenAI()` 客户端。
- 2. function tool `parameters` 过于空泛，缺少 `properties`。
- 3. tool output 以原生对象回传，Responses API 要求字符串。
- 4. `save_selected_papers` 只接受完整 paper payload，但模型真实会只传 `paper_ids`。
- Semantic Scholar 真实搜索会触发 429，必须在 scholarly tool 边界降级为紧凑 JSON 错误而不是中断整个阶段。
- 2026-03-08 23:52 +08，主题 `solid-state battery electrolyte` 的真实 live run 已成功返回完整 `RunResult`，包含 `selected_papers`、`evidence_cards`、`conflict_clusters`、`hypotheses` 和 `report_markdown`。
- 当前仍需确认真实运行路径是否把每次 tool call 正确持久化到 `tool_traces`，以满足 SPEC 的 trace 要求。
- 已确认真实运行路径的 trace 持久化修复生效：fresh run `run_6a638169c5c44fe28f02880d373d17ce` 当前数据库中已有 12 条 trace，覆盖 retrieval 多次检索和 review 的 `load_selected_papers`。
- `build_default_services()` 返回的 `ServiceContainer` 目前只暴露 `coordinator`，不暴露 `repository`；后续 fresh verification 需要通过 `coordinator` 或直接 `RunRepository` 访问数据库状态，而不是从 container 直接取 repository。
- 2026-03-09 00:03 +08 再次核验后，fresh run `run_6a638169c5c44fe28f02880d373d17ce` 已完成到 `done`，包含 20 篇 selected papers、12 张 evidence cards、5 个 conflict clusters、3 个 hypotheses，且 `tool_traces` 达到 19 条。
- 最新 trace 明确覆盖四个阶段：`retrieval`、`review`、`critic`、`planner`，说明真实路径的 trace 持久化已满足 SPEC 对完整 tool trace 的验收要求。
- FastAPI 读取端点 fresh verification 通过：`GET /v1/runs/{run_id}`、`GET /v1/runs/{run_id}/trace`、`GET /v1/runs/{run_id}/report.md` 均返回 200，报告长度为 3354 字符。
- 真实链路修复已提交并推送到远程：`67eb498 fix: harden live tool-calling workflow` 当前已在 `origin/main`。
- 基于 SPEC 第 16、17、18 节与 MVP 验收标准，当前最大的剩余差距不是四阶段能力本身，而是运行控制面：
- 1. cache 还未按 SPEC 形成明确的 raw response / normalized paper / evidence extraction 三层缓存；
- 2. budget 还未完整覆盖 per-run tool steps、外部源调用次数与超预算行为；
- 3. degradation 已有局部实现，但还没系统覆盖 retrieval/review/critic/planner 的全部降级分支；
- 4. trace 已可用，但离 SPEC 建议字段还差 `request_id`、更完整的 token 统计与阶段级日志汇总。
- 用户已确认下一阶段不做预算控制，因此当前实施范围收敛为：缓存、系统化降级、以及可观测性补齐。
- Phase 6 首轮 red test 已确认当前缺口集中在三处：
- 1. `hypoforge.infrastructure.db.cache_repository` 尚不存在；
- 2. `hypoforge.infrastructure.connectors.cached` 尚不存在；
- 3. 在补完上述模块后，还需要继续实现 coordinator 降级和 trace metadata 透传，才能使新增测试转绿。
- Phase 6 当前已完成的新增能力：
- 1. SQLite 持久化缓存仓储 `cache_entries`；
- 2. OpenAlex / Semantic Scholar 查询缓存与 normalized paper cache；
- 3. review 阶段 evidence cache 短路；
- 4. coordinator 对 critic 失败继续、planner 失败返回 partial result；
- 5. tool trace 现在能落 input/output tokens，并在 `/trace` 中暴露 `request_id`。
- 2026-03-09 00:22 +08 的 fresh real-run 审计显示：最新 run `run_13693266052340eaab98cfe1ed69a82a` 已完成 retrieval 并进入 `reviewing`，当前 `trace_count=12`，最新 trace 行已能看到非空 `request_id`。
- 2026-03-09 00:27 +08 再次审计后，`run_13693266052340eaab98cfe1ed69a82a` 已完成到 `done`，总 trace 为 19 条，包含 review/critic/planner 后续阶段，确认 Phase 6 改动后的真实链路仍可闭环。
- 真实 trace 中 token usage 为 0 的根因已定位：`OpenAIResponsesProvider._parse_response()` 在 `function_call` 分支提前返回，导致 tool-call turn 的 `usage` 没有带进 `ProviderTurn`，后续 `AgentRunner` 传给 tool invoker 的 trace context 始终为空。
- 修复后，fresh run `run_07bb6d6f867a42db99fcec9c5e3b83bb` 在 retrieval 阶段的 trace 已出现非零 `input_tokens=772`、`output_tokens=244`，说明 SPEC 第 17 节要求的 token 级 trace 现在在真实路径上生效。
- 当前测试缺口集中在“真实 API 端到端”这一层：现有 [`tests/integration/test_runs_api.py`](/Users/ccy/Documents/KEY/HypoForge/tests/integration/test_runs_api.py) 仅覆盖 fake coordinator，尚未有 env-gated 的真实 `POST /v1/runs` + `GET /v1/runs/{id}` + `/trace` + `/report.md` live integration test。
- 真实 API live test 暴露了新的数据层缺陷：`evidence_cards.id` 目前在数据库中是全局唯一，而真实模型会跨 run 重复生成 `EV001`、`EV002` 之类的 evidence id，导致第二次真实 run 在 review 阶段 `save_evidence_cards` 触发 `sqlite3.IntegrityError`。
- 同类风险也存在于 `conflict_clusters.id`，因为真实模型也常使用 `cluster_1` 这类跨 run 重复的标识；数据库行主键需要按 `run_id` 做 namespacing，而不是直接复用模型产出的业务 id。
- 现已新增 env-gated live integration test [`tests/live/test_real_runs_api.py`](/Users/ccy/Documents/KEY/HypoForge/tests/live/test_real_runs_api.py)，覆盖真实 `POST /v1/runs`、`GET /v1/runs/{id}`、`GET /v1/runs/{id}/trace`、`GET /v1/runs/{id}/report.md` 全链路。
- `evidence_cards` 与 `conflict_clusters` 的数据库主键冲突已通过 repository 行级 ID namespacing 修复：数据库层使用 `run_id:local_id` 作为 row id，业务 payload 仍保留模型原始 `EV001` / `cluster_1` 标识。
- fresh 全量验证已包含真实 API 路径：`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` 当前结果为 `41 passed in 156.79s`，说明 fake、unit、integration、e2e、live 五层测试当前可以一起通过。
- 当前剩余的 SPEC 差距更集中在两点：
- 1. “每阶段进入/退出、summary”的结构化记录还没有持久层落点，仍主要依赖日志和最终 artifacts；
- 2. review 阶段仍是一次性处理全量 selected papers，不具备 paper-batch / partial extraction / batch-level degrade 的能力。
- 当前第一轮修复设计如下：
- 1. 新增 `stage_summaries` 持久层记录，每阶段持久化 `status/summary/error_message/started_at/completed_at`；
- 2. `RunResult` 现在带回 `stage_summaries`，因此 API 读取结果时即可直接看到阶段级摘要；
- 3. review 改为按 `review_batch_size` 分批执行，批次失败时保留已成功 evidence，并通过 `ReviewSummary.failed_paper_ids` 明示 partial extraction。
- 真实 live test 进一步暴露：planner 的模型输出偶尔会遗漏 `counterevidence_ids`，这类缺口不应该让整条 run 失败；当前已在 `WorkspaceTools.save_hypotheses()` 入库边界加入 repair 逻辑，优先从相关 conflict clusters 的 `conflicting_evidence_ids` 自动补齐。
- fresh live verification 已确认上述修复有效：真实 API round-trip 和带 live 的全量测试当前都通过。
- 目前按 SPEC 剩余的高价值缺口主要落在 retrieval 侧：
- 1. 结果过少时还没有“一次自动放宽 query/year range”的恢复流程；
- 2. `coverage_assessment=low` 或 review partial extraction 当前并不会自动反映成结构化 stage summary 的 `degraded` 状态。
- 当前第一轮修复设计如下：
- 1. retrieval 首次结果低于阈值时，会自动执行一次放宽后的 second pass，目前先落到 `year_from - 5`；
- 2. second pass 仍低于阈值时，返回明确的 low-evidence mode，避免把低召回伪装成正常完成；
- 3. coordinator 现在会把 retrieval low-evidence 和 review partial extraction 映射成 `stage_summaries[*].status = degraded`。
- fresh live verification 已确认 retrieval recovery 没有破坏真实 API 路径：真实 round-trip 和带 live 的全量测试都已转绿。
- 当前按 SPEC 剩余的另一个高价值缺口是 `18.5 Structured Output 失败`：
- 1. `AgentRunner` 在输出 model 校验失败时还没有自动重试；
- 2. retrieval/review/critic/planner 还没有宿主侧 repair parse，只能依赖模型一次性命中严格 schema。
- 当前第一轮修复设计如下：
- 1. `AgentRunner` 在 final output 校验失败时，会自动追加一次“只返回修正后 JSON”的 retry turn；
- 2. retry 后仍然不合法时，进入宿主侧 `repair_output` 回调；
- 3. retrieval/review/critic/planner 分别挂轻量 repairer，优先补齐缺失字段和保守默认值，而不是强行篡改核心结论。
- fresh live verification 已确认 structured output recovery 没有破坏真实 API 路径：真实 round-trip 和带 live 的全量测试当前均通过。
- 当前按 SPEC 剩余的高价值缺口之一是 `18.4 planner failure` 的后半句：虽然 planner 失败时已经返回 partial result，但还没有“只重跑 planner”的显式入口。
- 当前第一轮修复设计如下：
- 1. 新增 `RunCoordinator.rerun_planner(run_id)`，复用现有 evidence/conflict 状态重新执行 planner；
- 2. 新增 `POST /v1/runs/{run_id}/planner/rerun`，返回更新后的 `RunResult`；
- 3. 若 rerun 前缺少 evidence cards，则返回冲突错误而不是静默执行。
- fresh live verification 已确认 planner rerun 改动没有破坏真实默认链路；这次真实 round-trip 偏慢，但最终仍通过。
- 当前按 SPEC 剩余的另一个核心缺口是第 16 节的外部 API 调用预算：配置字段已存在，但还没有真实 enforcement。
- 当前第一轮修复设计如下：
- 1. 新增 run-scoped `RunBudgetTracker`；
- 2. 预算只在 cached connector 发生 cache miss、即将真实出网时扣减；
- 3. 超限时通过 `BudgetExceededError` 走回工具层，返回结构化 `budget_exceeded` payload，而不是抛异常中断整阶段。
- 当前按 SPEC 剩余的高价值可信性缺口落在 18.3 / 19.2：
- 1. planner 在无 conflict map、低证据、partial review 时，还没有显式把限制和不确定性写进 hypothesis 本身；
- 2. 当前 `Hypothesis` schema 只要求 supporting/counterevidence/minimal_experiment，不足以把“provisional”状态传到最终报告；
- 3. 这类规则更适合先由宿主侧在 `save_hypotheses` 边界补齐，而不是一开始就要求真实模型稳定产出全部字段。
- 当前第一轮修复设计如下：
- 1. 为 `Hypothesis` 增加 `limitations` 与 `uncertainty_notes` 字段；
- 2. `WorkspaceTools.save_hypotheses()` 在 retrieval low-evidence、review degraded、critic degraded 或 conflict map 缺失时，自动补齐可信性说明；
- 3. 报告渲染层同步展示这些字段，避免 API 返回和 Markdown 报告语义脱节。
- 当前第一轮实现已完成：
- 1. `Hypothesis` 已新增 `limitations` / `uncertainty_notes`，且不破坏现有 payload 兼容性；
- 2. `save_hypotheses()` 现在会基于 `stage_summaries` 与 `conflict_clusters` 做宿主侧可信性标注；
- 3. 即使 planner 不主动输出 `risks`，宿主也会补一条保守风险说明，避免最终报告看起来比证据条件更“确定”。
- fresh verification 已确认上述 hardening 没有破坏真实 API 路径：本地全量为 `56 passed, 1 skipped`，live round-trip 为 `1 passed in 215.29s`，带 live 的全量为 `57 passed in 239.67s`。
- 当前相对 SPEC 剩余的主要后端缺口已经不在主链路，而在控制面尾差：
- 1. `AgentRunner` 的 `max_tool_steps` 现在会抛错，但还没有系统地转成“阶段结束并返回已有最优结果”；
- 2. 这意味着第 16.3 节的 API 预算已经闭环，但 `tool step budget` 只算半完成；
- 3. 这块补上后，MVP 级 backend 基本就只剩回归覆盖和前端接入问题了。
- 当前第一轮实现已完成：
- 1. `AgentRunner` 现在抛显式 `ToolStepBudgetExceededError`；
- 2. retrieval budget 超限会返回 partial `RetrievalSummary`，而不是继续 broaden retry 或直接整 run 失败；
- 3. review budget 超限会停止后续批次，返回已有 evidence 的 partial summary；
- 4. critic/planner budget 超限会优先返回已保存的 clusters / hypotheses，并把阶段标成 `degraded`。
- fresh verification 已确认 tool step budget 收束没有破坏真实 API 路径：本地全量为 `59 passed, 1 skipped`，live round-trip 为 `1 passed in 179.16s`，带 live 的全量为 `60 passed in 293.01s`。
- 当前按 SPEC 剩余最明显的测试缺口是第 22.2 / 24 节提到的 `5 个 golden topics` 回归集。
- 设计决定：
- 1. golden regression 作为单独 env-gated live suite 落在 `tests/live/`，避免把默认 live 测试时间抬得过高；
- 2. 单 topic live test 与 golden suite 共享 helper，统一断言 `done / selected papers >= 12 / hypotheses == 3 / report 非空 / trace 非空 / retrieval 多次 tool call`；
- 3. 默认 full pytest 仍保持轻量，golden suite 由显式环境变量触发。
- 当前第一轮实现已完成：
- 1. 新增 `hypoforge.testing.live_regressions`，统一 live topic 的 payload、断言和 DB 隔离；
- 2. `tests/live/test_real_runs_api.py` 已切换到共享 helper；
- 3. `tests/live/test_golden_topics_api.py` 现在对 5 个 golden topics 做参数化回归。
- 首次实跑 golden regression 的根因已定位：
- 1. 失败不是 retrieval/report/trace 层面，而是 planner 入库边界；
- 2. 两个 topic (`solid-state battery electrolyte`, `CO2 reduction catalyst selectivity`) 都在 `save_hypotheses` 因第 3 个 hypothesis 的 `supporting_evidence_ids < 3` 失败；
- 3. 当前 `WorkspaceTools._repair_hypothesis_payload()` 只修 `counterevidence_ids`，没有对不足的 supporting evidence 做宿主侧补全。
- 修复策略已验证有效：
- 1. 宿主侧现在会优先使用相关 conflict cluster 的 supporting 侧来补齐 `supporting_evidence_ids`；
- 2. 先前失败的两个 topic targeted rerun 已转绿；
- 3. 完整 5-topic golden regression 现已 `5/5` 通过。
- 默认全量测试也已重新确认通过，说明 golden regression 的 helper 和 planner repair 没有破坏日常测试面。
- 前端设计相关新发现：
- 1. `pbakaus/impeccable` 相关 skill 已经安装在本机，`frontend-design` 可直接使用，无需额外安装；
- 2. 这套 skill 强调的是有明确美学立场的、非模板化 dashboard，而不是默认深色霓虹或普通 SaaS 卡片堆叠；
- 3. 当前仓库仍然是 backend-only，没有现成前端壳子，因此需要先确定“内部研究工作台”还是“对外展示型产品页”为主。
- 用户已确认前端定位为“对外展示型 demo 产品页”，但核心受众是研究人员。
- 这意味着页面需要兼顾两类目标：
- 1. 对外展示：第一屏要快速说明 HypoForge 是什么、为什么可信；
- 2. 研究人员心智：中后段必须展示流程、trace、evidence、stage progress 和 hypotheses 产物，而不是纯营销文案。
- 用户进一步澄清：他要的不是介绍型网页，而是“操作界面”。
- 因此前端信息架构应直接以应用首页/dashboard 为中心，不再保留传统 landing page hero + 营销段落的模式。
- 用户继续确认了两个关键约束：
- 1. 前端第一版必须能直接输入 topic 并启动真实 run；
- 2. 整体结构采用“多视图控制台”，而不是单页堆叠工作台；
- 3. 页面必须可视化每一个阶段，而不是只显示最终 hypotheses。
- 用户对前端基底给出明确偏好：优先直接复用 [Kiranism/next-shadcn-dashboard-starter](https://github.com/Kiranism/next-shadcn-dashboard-starter)，并只做最小必要调整。
- 这意味着前端策略应从“完全原创 dashboard shell”收敛为“复用成熟开源壳子 + 定制 HypoForge 的信息架构和研究工作流视图”。
- 用户已确认为前端补一个最小后端扩展：新增 `GET /v1/runs` 列表接口。
- 因此前端 `Runs` 页面可以基于服务端真实历史数据实现，而不是只依赖浏览器本地缓存。
- 用户再次明确要求按既定方案执行，不能在实现前偏离这套边界：
- 1. `New Run`
- 2. `Runs`
- 3. `Run Detail / Overview`
- 4. `Trace`
- 5. `Report`
- 当前这版方案已经足以进入实现，不需要再继续发散式设计讨论。
- starter 的当前结构与这套方案是匹配的：
- 1. `src/app/dashboard/layout.tsx` 可直接承载 HypoForge 的 app shell；
- 2. `src/config/nav-config.ts` 可以轻量改成 `New Run` / `Runs`；
- 3. `react-resizable-panels` 适合 `Trace` 的左右分栏；
- 4. `@tanstack/react-table` 适合 `Runs` 列表；
- 5. 需要移除 `@clerk/nextjs` 认证门禁，否则和当前 backend-only demo 冲突。
- 视觉边界也已经固定，不应再摇摆：
- 1. 默认浅色；
- 2. 学术编辑台；
- 3. 纸白、墨蓝灰、氧化青、赭红；
- 4. `Newsreader + IBM Plex Sans`；
- 5. 不是工业控制台，也不是营销页。
- `SPEC.md` 明确“不做复杂前端”，因此前端第一版只做薄壳消费 API，这和当前已确认的方案完全一致。
- 面向前端的第一批最小后端扩展已经落地并转绿：
- 1. 新增 `RunSummary` / `RunSummaryBody`；
- 2. `GET /v1/runs` 已可返回 runs 列表；
- 3. `RunCoordinator` / `RunRepository` 已暴露列表能力；
- 4. FastAPI 已支持可配置 CORS，适合本地 `frontend` 直接联调。
- 前端当前已经不再是纯 scaffold，而是可运行的真实工作台：
- 1. `New Run` 可直接发起真实 `POST /v1/runs`；
- 2. `Runs` 消费 `GET /v1/runs` 展示真实历史；
- 3. `Run Overview` 消费 `GET /v1/runs/{id}` 展示 stage summaries 与结果摘要；
- 4. `Trace` 消费 `GET /v1/runs/{id}/trace`；
- 5. `Report` 消费 `GET /v1/runs/{id}/report.md`。
- starter 残留的 demo 代码很多，如果全部纳入 TS/ESLint 会拖累验证链；当前已通过 `tsconfig` / ESLint ignore 只保留 HypoForge 实际运行路径的检查面。
- 当前前端验证面是稳定的：
- 1. `npx tsc --noEmit` 通过；
- 2. `npm run lint` 通过；
- 3. `npm run build` 通过；
- 4. backend 契约相关测试 `13 passed`。
- 前后端联调 smoke 也已通过：
- 1. `http://127.0.0.1:3000/` 会重定向到 `/dashboard/new-run`；
- 2. `http://127.0.0.1:3000/dashboard/new-run` 正常返回 `HypoForge Console`；
- 3. `http://127.0.0.1:8000/v1/runs` 正常返回真实 run 列表。
- 当前已知非阻断项只有一个：`baseline-browser-mapping` 过旧提示，会在 build 时重复打印，但不影响产物和路由生成。
- Phase 17 full verification 首轮暴露出的唯一真实回归是 retrieval under-select：在 `diffusion model preference optimization` 上，模型偶尔不会把 candidate pool 用满，导致 selected papers 数量低于 golden regression 要求的 12 篇。
- 为保持 SPEC 门槛不变，已在 retrieval 边界加入宿主侧补位：若 broadened retrieval 后 repository 中 selected papers 仍未达到阈值，则从现有 candidate pool 按 `dedupe + ranking` 规则补齐，并把该动作写入 `search_notes`。
- 前端 overflow 的主因已经确认：
- 1. `app-sidebar.tsx` 折叠态误用了 `group-data-[collapsible=icon]/sidebar:*`，导致文本在 48px 宽的 icon rail 中继续显示；
- 2. `golden-topic-launcher.tsx` 的长主题按钮未允许换行；
- 3. `new-run-form.tsx` 的底部说明和按钮在较窄宽度下仍强制横向排布；
- 4. `info-sidebar.tsx` 还保留了 `/SPEC.md` 和本地 docs 的断链。
- 上述 overflow 与断链都已修复，并在 1024px / 768px 浏览器截图中复查通过。
- 用户新反馈的“浏览器右侧大面积空白”已定位为 shell-level 布局问题，而不是单个组件宽度问题。
- 直接原因：
- 1. `frontend/src/app/dashboard/layout.tsx` 一直挂着 `InfoSidebar`；
- 2. `frontend/src/components/ui/infobar.tsx` 的 desktop 模式会为 infobar 预留固定宽度轨道；
- 3. 因此即使主页面本身没有内容，也会像“右边留白”。
- 修复策略：
- 1. 第一版控制台取消全局常驻右侧 infobar；
- 2. 页面辅助说明回收到主内容区；
- 3. 只有在真正需要 inspector 的详情页里再考虑局部侧栏，而不是由 shell 永久占位。

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 采用 Python 包式 `src/` 布局并拆分 app/domain/infrastructure/interfaces | 对应 SPEC 的 API、Coordinator、Agent Runtime、Tool Host、Workspace Store 分层 |
| 先设计可替换 provider 抽象，再接 OpenAI/OpenAlex/S2 | 便于 TDD、离线测试与后续真 API 接入 |
| 以 SQLite 作为默认持久层 | 与 SPEC 一致，且适合 MVP |
| 默认远程仓库目标为 GitHub 私有仓库 `HypoForge` | 用户已确认按默认假设继续 |
| 使用 `.venv` + Python 3.12 作为本地执行环境 | 满足 SPEC 推荐版本并避开系统 Python 3.9 |
| 默认运行时接真实 provider/connector 边界，默认验证路径使用 fake services | 保持真实集成入口，同时避免本地验证依赖外部密钥和网络 |
| 真实 retrieval 候选池保存在 `build_default_services()` 的 `run_id` 级闭包缓存中 | 允许模型只用 `paper_ids` 调用 `save_selected_papers`，更贴近真实 tool-calling 行为 |
| 前端单独放在仓库顶层 `frontend/` 目录 | 避免 Python 打包环境和 Next 构建环境互相污染 |
| 全局导航只保留 `New Run` / `Runs`，run 详情内部再切 `Overview` / `Trace` / `Report` | 更符合研究工作流，不会让用户在全局层级迷失当前 run 上下文 |
| 前端先通过 `NEXT_PUBLIC_API_BASE_URL` 直连后端 API，必要时补 CORS | 比在 Next 内再加一层代理更直接，适合第一版 demo |
| Run 列表接口返回轻量 summary，而不是完整 `RunResult` | 避免 `Runs` 页面加载过重，也让路由契约更稳定 |
| 先保留 starter 的部分未使用依赖与组件文件，但通过路由清理和 lint/type exclusion 隔离掉 demo 噪音 | 更符合“最小必要调整”，避免把时间浪费在不影响当前功能的模板大清扫上 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| 当前目录不是 Git 仓库 | 记录为待办，在实现完成后初始化并推送 |
| 远程仓库信息未知 | 需要在设计确认阶段明确或采用默认假设 |
| Git 提交缺少 `user.name` / `user.email` | 通过 `gh api user` 读取当前账号资料，并在仓库本地设置提交身份 |
| Semantic Scholar 429 直接打断 retrieval | 在 `ScholarlyTools` 增加统一 HTTP 降级包装，返回 `{\"papers\": [], \"error\": ...}` |
| Responses API 拒绝 strict output schema | 在 provider 中递归补齐 `additionalProperties: false` 与完整 `required` |
| 模型真实只传 `paper_ids` 给 `save_selected_papers` | 在 `build_default_services()` 增加 `run_id` 级候选池缓存，并由 tool host 解析 |
| 真实路径没有保存 tool traces | 在默认服务 `make_tool_invoker()` 中按调用记录 args、摘要、耗时、模型名和成功状态 |
| fresh verification 脚本直接访问 `services.repository` 失败 | 改为使用 `services.coordinator` 或单独构造 `RunRepository` 读取最新 run / trace |
| fresh verification 脚本直接访问 `repo.get_latest_runs()` 失败 | `RunRepository` 并未暴露该 helper，改为通过 `RunRow.created_at` 底层查询最新 run |
| starter 默认启用 Clerk | 当前项目不做认证，因此实现时需要移除该依赖和相关路由守卫 |
| starter 默认 ESLint 配置与当前 `eslint-config-next` 组合会报 circular structure | 已替换为更简单稳定的 TypeScript ESLint 配置，并把未接入的 demo 目录排除在 lint 外 |

## Resources
- SPEC: `/Users/ccy/Documents/KEY/HypoForge/SPEC.md`
- planning-with-files skill: `/Users/ccy/.codex/skills/planning-with-files/SKILL.md`
- brainstorming skill: `/Users/ccy/.codex/superpowers/skills/brainstorming/SKILL.md`
- test-driven-development skill: `/Users/ccy/.codex/superpowers/skills/test-driven-development/SKILL.md`
- design doc: `/Users/ccy/Documents/KEY/HypoForge/docs/plans/2026-03-08-hypoforge-design.md`
- implementation plan: `/Users/ccy/Documents/KEY/HypoForge/docs/plans/2026-03-08-hypoforge-mvp.md`
- frontend design doc: `/Users/ccy/Documents/KEY/HypoForge/docs/plans/2026-03-09-hypoforge-frontend-design.md`
- frontend implementation plan: `/Users/ccy/Documents/KEY/HypoForge/docs/plans/2026-03-09-hypoforge-frontend-implementation.md`
- frontend app root: `/Users/ccy/Documents/KEY/HypoForge/frontend`

## Visual/Browser Findings
- 无
- 2026-03-09 18:15 +08 前端全面 polish 的关键发现：
- 1. `Runs` 页不仅有 overflow 问题，也有信息层级过于模板化的问题；历史失败 run 的长错误应作为二级上下文，而不是主导整行布局。
- 2026-03-09 19:08 +08 新一轮前端 polish 的关键发现：
- 1. run 详情页缺少 `topic`，导致 `Overview / Trace / Report` 只能共享一个通用标题，dossier 识别度不够；
- 2. `New Run` 的右栏只有流程说明，缺少启动前的操作性提示，像说明书而不像控制台；
- 3. sidebar footer 仍写着 `Demo mode`，和当前真实 API 运行路径不一致；
- 4. `Trace / Report` 需要比“单纯正文”更多一层研究语义摘要，帮助研究人员快速判断是否值得继续深挖。
- 2026-03-09 19:23 +08 现有“流程可视化”只做了一半：详情页本身会轮询 `run/trace/report`，但 `New Run` 仍调用同步 `POST /v1/runs`，所以用户在点击启动后要等整个 run 完成，无法看到 retrieval -> review -> critic -> planner 的实时推进过程。
- 2026-03-09 19:35 +08 异步 launch 打通后，新的短板变成“运行中态反馈仍偏弱”：虽然页面会轮询，但 `Overview / Trace / Report` 在 run 进行中还缺少足够明确的 live 文案、占位内容和当前阶段强调，用户仍会感觉页面像静态结果页。
- 2026-03-09 19:45 +08 live dossier 做完后，archive 仍然偏“查历史”，对正在运行的条目不够友好；用户还需要一个不翻整张表就能直接回到 in-flight run 的入口，以及更明显的 active 状态标记。
- 2026-03-09 19:54 +08 archive 和 live-state 都补齐后，剩下的差异主要是“时间感”：用户能看见阶段和 trace，但还需要更明确知道哪一个阶段是刚更新的、哪一条 trace 是最新活动，而不是自己盯着列表猜。
- 2026-03-09 20:02 +08 在时间感补齐后，最后的短板变成“进入和加载的质感不统一”：`Runs` 还缺少真正的 skeleton archive，`Overview` 和 `Trace` 的状态变化虽然清楚，但仍然偏静态，没有统一的轻量进入节奏。
- 2026-03-09 20:14 +08 真实 demo walkthrough 结论：当前前后端联动已经能支撑完整演示，launch 后 run 会立即进入 live dossier，真实状态会依次推进到 `done`，并且产物能够回写 archive、trace 和 report 视图。

## Latest Decisions
- 2026-03-09 19:09 +08 决定把 `RunResult` 扩成真正可供详情页消费的 dossier 头部数据，至少带回 `topic`；这类信息不应再让前端依赖 run list 上下文拼接。
- 2026-03-09 19:10 +08 本轮前端打磨继续遵循“最小改动 starter 壳，只优化信息层与语义摘要”的边界，不引入新的前端框架或大规模壳层重构。
- 2026-03-09 19:14 +08 `RunHero` 统一改为 topic 驱动标题，`New Run` 增加 `Launch profile`，`Trace` 增加 `Cache hits`，`Report` 增加 `Uncertainty notes`，作为研究工作流的高价值摘要层。
- 2026-03-09 19:24 +08 决定采用“兼容式异步启动”而不是直接改写原有 `POST /v1/runs`：同步入口继续服务现有 live tests 和脚本，新增 `/v1/runs/launch` 专供前端使用，避免破坏既有回归套件。
- 2026-03-09 19:28 +08 异步 launch 落地后，前端点击 `Launch live run` 会立即进入 `/dashboard/runs/{run_id}`；详情页已有的 `useRun()` / `useRunTrace()` / `useRunReport()` 轮询机制开始接管真实阶段可视化。
- 2026-03-09 19:36 +08 当前前端运行中态的设计决策是：不再新增独立 loading 页面，而是在现有 `Overview / Trace / Report` 内部分别补 `live banner + skeleton + pending copy`，让用户始终留在同一个 dossier 语境里。
- 2026-03-09 19:46 +08 `Runs` 页当前的设计决策是“archive + live docket”双层结构：顶部先给正在运行的 dossier 快速入口，下面保留完整归档，并用轻量筛选切换 `All / Active / Completed / Failed`。
- 2026-03-09 19:55 +08 最后一层时间感反馈的设计决策是“轻量提示，不额外加新页面”：在 `Overview` 里用 `Receiving updates now / Updated x ago` 和默认展开当前/异常阶段，在 `Trace` 里对最新条目增加 `Latest` 标记和更强的 live 高亮。
- 2026-03-09 20:03 +08 最终成品感收口的设计决策是“轻 motion，不卡性能”：采用 `motion/react` 做 0.22s 级别的 stagger entrance，仅用于阶段卡片和 trace 条目；`Runs` 的 loading 改成 skeleton archive，而不是额外引入新的 loading 页面。
- 2026-03-09 20:14 +08 walkthrough 期间需要注意的一点是：本地 8000 端口如果仍在跑旧版 uvicorn，会导致 `/v1/runs/launch` 返回 405；重新启动后即可正常进入异步 launch 流程。这是本地运行态问题，不是代码路径缺失。
- 2. `Overview / Trace / Report` 虽然已经可用，但原始 JSON 和阶段状态过于“裸露”，研究人员需要更可读的摘要映射，而不是直接面对后端字段名。
- 3. `StageProgressBand` 在 1024px 仍然四列展示会让 `critic/planner` 长文案变成窄高条，属于密度过高而非严格 overflow，但会显著损害可读性。
- 4. 当前前端仍没有独立 test runner；这轮按既有约束使用 `lint + build + Playwright breakpoint inspection` 作为验证路径，没有临时引入新的测试栈。
- 5. 在超宽屏下，右侧空白不只是 shell gutter 的问题，run 相关页面自己的 `max-w-[1680px]` 也是第二层限制；即使 shell 已经铺开，内容区仍会被内部 container 再次截短。
- 6. 仅仅移除固定 `max-width` 也不够，这会把问题从“太窄”推到“过满”；正确做法是流体宽度算法，兼顾可用宽度、超宽屏阅读边距和自动居中。
- 7. 流体宽度算法也不能直接用 `100vw`。在带 sidebar 的 dashboard shell 里，`vw` 看到的是整个浏览器，而不是主内容父容器；这会把内容算得比实际可用宽度更宽。
- 2026-03-10 多课题真实 live 验证结论：
- 1. 当前前后端链路已经具备真实 end-to-end 可运行性，因为 5 个真实课题里有 4 个完成了完整的 `launch -> polling -> trace -> report -> archive -> frontend routes` 流程。
- 2. 但还不能宣称“所有真实研究课题都稳定跑通”，因为 `diffusion model preference optimization` 在 planner 阶段失败。
- 3. 该失败不是路由、前端页面、trace 持久化或 report 读取问题；这些都正常返回。
- 4. 根因位于 planner 输出质量和宿主侧 hypothesis 校验边界：单个 hypothesis 没有满足“至少 3 个 supporting evidence ids”的硬约束。
- 5. 当前系统状态应表述为“端到端可运行，但多 topic live 稳定性仍有最后一处 planner fallback 缺口”。
- 2026-03-10 planner 低证据 fallback 修复后的新发现：
- 1. 不需要放松 `Hypothesis` schema 约束；保留“至少 3 个 supporting evidence ids”可以继续作为质量门槛。
- 2. 更合理的修复点在 `WorkspaceTools.save_hypotheses()`：先推断 supporting evidence，再在 distinct evidence 不足时做受控补位，并明确写入 limitation。
- 3. 这条修复已经在先前失败的真实 topic `diffusion model preference optimization` 上 fresh 复现并转绿。
- 4. 因此当前剩余的不确定性不再是“这个 topic 会不会继续失败”，而是“整批多 topic 重跑后的总体 success rate 是否稳定提升”；这需要整批 rerun 才能证明。
- 2026-03-10 对照 SPEC 原意后的最终判断：
- 1. “重复 evidence id 补位”虽然提高了 live success rate，但不符合第 8.4、19.1、19.2、23 节对 grounding 和 hypothesis 质量的真实要求。
- 2. 因此当前正式策略改为严格派：至少 3 个 distinct supporting evidence ids 才算有效 grounding。
- 3. 在 strict 模式下，低证据 topic 重新失败是可接受的，因为这比伪造证据强度更符合 HypoForge 的产品定位。
- 4. 当前更高优先级是“诚实降级 + planner rerun”，而不是“强行把所有 topic 都跑成 done”。
- 2026-03-10 strict 扩样后的新发现：
- 1. 严格派并没有像先前担心的那样显著降低 live success rate；在 8-topic batch 中当前结果是 `8/8 done`。
- 2. 这说明之前那个 planner grounding 失败更像是偶发真实边界问题，而不是 strict 语义本身必然导致大面积失败。
- 3. 当前可以更有信心地说：strict grounding 和可运行性并不冲突，至少在现阶段这 8 个真实 topic 上是兼容的。

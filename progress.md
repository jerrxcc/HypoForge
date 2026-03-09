# Progress Log

## Session: 2026-03-08

### Phase 1: Requirements & Discovery
- **Status:** in_progress
- **Started:** 2026-03-08
- Actions taken:
  - 读取并提炼 `using-superpowers`、`planning-with-files`、`brainstorming`、`test-driven-development` 技能说明。
  - 检查当前目录内容与 Git 状态，确认项目为空目录且尚未初始化 Git。
  - 分段阅读 `SPEC.md`，抽取架构、阶段流程、工具设计和数据模型约束。
  - 创建 `task_plan.md`、`findings.md`、`progress.md` 作为持久化工作记忆。
  - 读取 `writing-plans` 技能说明，确定设计确认后需要将实现方案写入 `docs/plans/YYYY-MM-DD-*.md`。
  - 补充 SPEC 的 API、数据库、配置与测试要求，并确认远程同步默认采用 GitHub 私有仓库 `HypoForge`。
- Files created/modified:
  - `task_plan.md` (created)
  - `findings.md` (created)
  - `progress.md` (created)

### Phase 2: Design & Plan
- **Status:** complete
- Actions taken:
  - 基于完整 SPEC 提炼出推荐架构：`src/` 包布局、四阶段 coordinator、provider-backed agent runner、typed tools、SQLite repository、deterministic renderer。
  - 输出设计文档 `docs/plans/2026-03-08-hypoforge-design.md`。
  - 输出实施计划 `docs/plans/2026-03-08-hypoforge-mvp.md`。
- Files created/modified:
  - `docs/plans/2026-03-08-hypoforge-design.md` (created)
  - `docs/plans/2026-03-08-hypoforge-mvp.md` (created)

### Phase 3: TDD Implementation
- **Status:** in_progress
- Actions taken:
  - 创建 `pyproject.toml`、`.env.example`、`.gitignore`、`README.md`、Task 1 的测试文件。
  - 使用 `python3.12 -m venv .venv` 建立虚拟环境，并安装项目及开发依赖。
  - 运行 Task 1 测试并确认按预期失败：`ModuleNotFoundError: No module named 'hypoforge'`。
  - 补充最小实现：`Settings`、FastAPI app factory、`/healthz` 路由。
  - 重跑 Task 1 测试并转绿。
  - 建立完整 domain schemas、SQLite repository、OpenAlex/Semantic Scholar connectors、typed tools、scripted/openai providers、agent runner、report renderer、coordinator、run APIs。
  - 增加 fake services 与 CLI runner，形成不依赖外部密钥的端到端验证路径。
  - 修复报告状态漂移问题和 fake evidence/cluster ID 冲突问题。
- Files created/modified:
  - `pyproject.toml` (created)
  - `.env.example` (created)
  - `.gitignore` (created)
  - `README.md` (created)
  - `src/hypoforge/__init__.py` (created)
  - `src/hypoforge/config.py` (created)
  - `src/hypoforge/api/app.py` (created)
  - `src/hypoforge/api/routes/health.py` (created)
  - `tests/unit/test_config.py` (created)
  - `tests/integration/test_health_api.py` (created)
  - `src/hypoforge/domain/` (created)
  - `src/hypoforge/infrastructure/` (created)
  - `src/hypoforge/tools/` (created)
  - `src/hypoforge/agents/` (created)
  - `src/hypoforge/application/` (created)
  - `src/hypoforge/api/routes/runs.py` (created)
  - `scripts/run_topic.py` (created)
  - `tests/unit/*` (expanded)
  - `tests/integration/*` (expanded)
  - `tests/e2e/test_end_to_end.py` (created)

### Phase 4: Git & Remote Sync
- **Status:** complete
- Actions taken:
  - 确认 `gh auth status` 已登录账号 `jerrxcc`，可直接创建 GitHub 私有仓库。
  - 初始化本地 Git 仓库并确认分支为 `main`。
  - 使用 `gh api user` 读取账号资料后，在仓库本地设置 Git 提交身份 `Cyrus <chu.yue@foxmail.com>`。
  - 创建根提交 `6b193c4 feat: initialize HypoForge MVP`。
  - 创建并推送 GitHub 私有仓库 `https://github.com/jerrxcc/HypoForge.git`。
- Files created/modified:
  - `task_plan.md` (updated)

### Phase 5: Verification & Delivery
- **Status:** complete
- Actions taken:
  - 全量测试、CLI smoke、`uvicorn` 启动验证均已完成。
  - 进入真实 OpenAI/OpenAlex/S2 live run 调试，按 `systematic-debugging` 方式逐个定位阻塞点。
  - 新增 provider 单测与 tool schema 单测，修复 `OPENAI_API_KEY` 透传、tool JSON schema、tool output 编码、strict response schema 合法化、候选池 `paper_ids` 解析、Semantic Scholar 429 降级。
  - 用户要求“每次改动都及时用 plan with file 进行记录”，已将其纳入当前工作方式。
  - 真实 OpenAI/OpenAlex/S2 live run 首次成功跑通，`topic=solid-state battery electrolyte` 返回完整 `RunResult`，状态为 `done`，并产出 16 篇 selected papers、16 张 evidence cards、4 个 conflict clusters 和 3 个 hypotheses。
  - 已补齐默认真实路径的 tool trace 记录逻辑，并通过数据库验证 fresh run `run_6a638169c5c44fe28f02880d373d17ce` 已持久化 12 条 trace。
  - 下一步继续等待这次 fresh run 完成，并再做 API 层 fresh 验证。
  - 复查服务装配层后确认 `ServiceContainer` 仅暴露 `coordinator`；fresh verification 需要改走 `coordinator` 或单独构造 `RunRepository` 查询数据库状态。
  - 使用 `RunRow.created_at` 底层查询确认 fresh run `run_6a638169c5c44fe28f02880d373d17ce` 已完成到 `done`，并具有 19 条 trace、20 篇 selected papers、12 张 evidence cards、5 个 conflict clusters、3 个 hypotheses。
  - 使用 FastAPI `TestClient` 对 `GET /v1/runs/{id}`、`GET /v1/runs/{id}/trace`、`GET /v1/runs/{id}/report.md` 做 fresh verification，三者均返回 200。
  - 重新执行全量测试 `./.venv/bin/pytest -v`，当前结果为 `28 passed in 0.49s`。
  - 提交真实链路修复为 `67eb498 fix: harden live tool-calling workflow`，并已推送到 `origin/main`。
  - 基于 SPEC 第 16/17/18 节重新评估后，记录下一阶段建议为 `SPEC Hardening`：优先补缓存、预算控制、系统化降级和可观测性，而不是先扩展新功能面。
  - 用户确认预算控制暂缓，因此当前继续实现的 Phase 6 范围调整为：缓存、系统化降级、可观测性。
  - 为 Phase 6 新增缓存、降级、trace metadata 测试，并执行首轮 red test；当前按预期失败于 `cache_repository` 与 `cached connectors` 模块缺失。
  - 已完成缓存仓储、缓存连接器、review evidence cache、coordinator 关键降级和 trace metadata 透传的实现；对应新增测试现已通过。
  - fresh 全量测试结果更新为 `34 passed in 0.57s`。
  - 真实 live run 正在执行，用于确认新缓存和降级逻辑未破坏默认真实链路。
  - 截至 2026-03-09 00:22 +08，最新真实 run `run_13693266052340eaab98cfe1ed69a82a` 已推进到 `reviewing`，并已记录 12 条新版 trace；其中已可见 `request_id` 字段，但 run 尚未完成到 `done`。
  - 最新真实 run `run_13693266052340eaab98cfe1ed69a82a` 随后已完成到 `done`，总 trace 数为 19，确认缓存/降级增强没有破坏真实默认服务路径。
  - 已定位并修复 provider 在 tool-call turn 丢失 usage 的问题；fresh run `run_07bb6d6f867a42db99fcec9c5e3b83bb` 的 retrieval traces 现已出现非零 token usage。
  - 下一步转向补齐真实 API 端到端 live integration test，目标是让真实 `POST /v1/runs` 与后续读取接口形成可重复的自动化验证，而不是只靠临时脚本。
  - 真实 API live test 已启动，但 fresh run `run_07bb6d6f867a42db99fcec9c5e3b83bb` 在 review 阶段失败；数据库错误确认根因是 `evidence_cards.id` 全局唯一导致跨 run 的 `EV001` 冲突。
  - 为 repository 新增重复 evidence/cluster id 的 red tests，并定位需要在持久层而不是模型层做 ID namespacing。
  - 已将 `evidence_cards`、`conflict_clusters` 的数据库 row id 改为 `run_id:local_id` 形式，保留 payload 中的原始业务 ID 不变。
  - 已新增 env-gated live integration test `tests/live/test_real_runs_api.py`，覆盖真实 `POST /v1/runs`、`GET /v1/runs/{id}`、`GET /v1/runs/{id}/trace` 与 `GET /v1/runs/{id}/report.md`。
  - 单独真实 API live test 已通过，耗时 `178.48s`。
  - 带真实 API 的全量测试已通过，结果为 `41 passed in 156.79s`；当前范围内的“真实 API 接入完整跑通”已完成。
  - 用户已同意继续按 SPEC 完善，当前开始下一轮 hardening：结构化阶段 summary 持久化，以及 review 分批抽取与 partial extraction。
  - 已新增 `tests/unit/test_stage_summaries.py`、`tests/unit/test_review_batches.py`，并扩展 `tests/integration/test_coordinator.py`，以 TDD 固定阶段摘要持久化和 review 批次聚合行为。
  - 当前 focused tests 已通过，结果为 `10 passed in 0.23s`。
  - 真实 live test 发现 planner 偶发漏填 `counterevidence_ids`，导致 `save_hypotheses` 校验失败；已在 workspace tools 增加基于 conflict clusters 的 repair。
  - fresh real API round-trip 已恢复通过，结果为 `1 passed in 173.55s`。
  - 带真实 API 的全量 fresh verification 已通过，结果为 `45 passed in 186.22s`。
  - 当前开始 Phase 8，目标是按 SPEC 18.1 补 retrieval low-evidence recovery，并把非异常型降级映射到 stage summary。
  - 已新增 `tests/unit/test_retrieval_recovery.py` 和 `tests/integration/test_stage_degradation_status.py`，固定 retrieval broaden retry 与 degraded stage summary 行为。
  - 当前 focused tests 已通过，结果为 `6 passed in 0.27s`。
  - fresh 全量本地测试已通过，结果为 `47 passed, 1 skipped in 0.63s`。
  - fresh 真实 API round-trip 已通过，结果为 `1 passed in 206.52s`。
  - 带真实 API 的全量 fresh verification 已通过，结果为 `48 passed in 236.87s`。
  - 当前开始 Phase 9，目标是按 SPEC 18.5 补 structured output retry 和 repair parse。
  - 已扩展 `tests/integration/test_agent_runner.py`，覆盖 structured output 自动重试和 retry 后 repair parse 两条恢复路径。
  - 当前 focused tests 已通过，结果为 `4 passed in 0.05s`。
  - fresh 全量本地测试已通过，结果为 `49 passed, 1 skipped in 0.63s`。
  - fresh 真实 API round-trip 已通过，结果为 `1 passed in 235.53s`。
  - 带真实 API 的全量 fresh verification 已通过，结果为 `50 passed in 228.74s`。
  - 当前开始 Phase 10，目标是按 SPEC 18.4 增加 planner-only rerun。
  - 已扩展 `tests/integration/test_coordinator_degradation.py` 和 `tests/integration/test_runs_api.py`，覆盖 coordinator rerun 与 API rerun 路径。
  - 当前 focused tests 已通过，结果为 `6 passed in 0.29s`。
  - fresh 全量本地测试已通过，结果为 `51 passed, 1 skipped in 0.66s`。
  - fresh 真实 API round-trip 已通过，结果为 `1 passed in 452.52s`。
  - 带真实 API 的全量 fresh verification 已通过，结果为 `52 passed in 296.65s`。
  - 当前开始 Phase 11，目标是把 OpenAlex / Semantic Scholar 的外部 API 调用预算从配置项做成真实 enforcement。
  - 已新增 `tests/unit/test_budget.py`，并扩展 `tests/unit/test_cached_connectors.py`、`tests/unit/test_scholarly_tools.py`，覆盖 budget tracker、cache miss 扣费和 `budget_exceeded` 返回。
  - 当前 focused tests 已通过，结果为 `10 passed in 0.19s`。
- Files created/modified:
  - `task_plan.md` (updated)
  - `findings.md` (updated)
  - `progress.md` (updated)
  - `tests/unit/test_openai_provider.py` (created)
  - `tests/unit/test_tool_schemas.py` (created)
  - `src/hypoforge/agents/providers.py` (updated)
  - `src/hypoforge/agents/runner.py` (updated)
  - `src/hypoforge/application/services.py` (updated)
  - `src/hypoforge/tools/schemas.py` (updated)
  - `src/hypoforge/tools/scholarly_tools.py` (updated)
  - `task_plan.md` (updated again)
  - `findings.md` (updated again)
  - `progress.md` (updated again)
  - `src/hypoforge/infrastructure/db/repository.py` (updated)
  - `tests/unit/test_repository.py` (updated)
  - `tests/live/test_real_runs_api.py` (created)
  - `README.md` (updated)
  - `.env.example` (updated)
  - `src/hypoforge/domain/schemas.py` (updated)
  - `src/hypoforge/infrastructure/db/models.py` (updated)
  - `src/hypoforge/infrastructure/db/repository.py` (updated again)
  - `src/hypoforge/application/coordinator.py` (updated)
  - `src/hypoforge/application/services.py` (updated again)
  - `src/hypoforge/tools/workspace_tools.py` (updated)
  - `src/hypoforge/tools/schemas.py` (updated)
  - `src/hypoforge/config.py` (updated)
  - `tests/unit/test_stage_summaries.py` (created)
  - `tests/unit/test_review_batches.py` (created)
  - `tests/unit/test_workspace_tools.py` (created)
  - `tests/integration/test_coordinator.py` (updated)

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Git workspace check | `git status --short --branch` | 若已初始化则返回分支状态 | 返回 `fatal: not a git repository` | observed |
| Task 1 red | `./.venv/bin/pytest tests/unit/test_config.py tests/integration/test_health_api.py -v` | 因缺少实现而失败 | `ModuleNotFoundError: No module named 'hypoforge'` | pass |
| Task 1 green | `./.venv/bin/pytest tests/unit/test_config.py tests/integration/test_health_api.py -v` | 两项测试通过 | `2 passed in 0.12s` | pass |
| Full pytest | `./.venv/bin/pytest -v` | 全量测试通过 | `20 passed in 0.32s` | pass |
| Fake CLI smoke | `./.venv/bin/python scripts/run_topic.py "solid-state battery electrolyte" --fake --database-url sqlite:///./hypoforge.cli.smoke.db` | 输出完成 run 且 hypotheses=3 | 返回 `status=done`、`hypothesis_count=3` 并打印报告 | pass |
| Uvicorn boot | `./.venv/bin/uvicorn hypoforge.api.app:create_app --factory --host 127.0.0.1 --port 8000` | 应用成功启动 | 日志显示 `Application startup complete`，随后正常 Ctrl-C 退出 | pass |
| GitHub auth | `gh auth status` | 当前账号已登录且具备 repo scope | 已登录 `jerrxcc`，scope 含 `repo` | pass |
| Remote push | `gh repo create HypoForge --private --source=. --remote=origin --push` | 远程仓库创建并推送成功 | `HEAD -> main` 且已设置跟踪分支 | pass |
| OpenAI provider config red-green | `./.venv/bin/pytest tests/unit/test_openai_provider.py -v` | provider 正确透传 key/base_url 并生成合法 response format | 单测通过 | pass |
| Tool schema red-green | `./.venv/bin/pytest tests/unit/test_tool_schemas.py -v` | function schema 包含真实 properties | 单测通过 | pass |
| Scholarly tools red-green | `./.venv/bin/pytest tests/unit/test_scholarly_tools.py -v` | 429 降级和 `paper_ids` 候选池解析均通过 | 单测通过 | pass |
| Agent runner red-green | `./.venv/bin/pytest tests/integration/test_agent_runner.py -v` | tool outputs 以字符串形式回传 provider | 集成测试通过 | pass |
| Real live run | `./.venv/bin/python - <<'PY' ... build_default_services().coordinator.run_topic('solid-state battery electrolyte') ... PY` | 返回完整真实 `RunResult` | `status='done'`，并返回 papers/evidence/conflicts/hypotheses/report | pass |
| Trace persistence fresh check | `./.venv/bin/python - <<'PY' ... sqlite query latest run + tool_traces ... PY` | 最新 run 至少已有非空 trace | 最新 run `run_6a638169c5c44fe28f02880d373d17ce` 处于 `reviewing`，trace_count=12 | pass |
| Full pytest after live-run fixes | `./.venv/bin/pytest -v` | 全量测试通过 | `28 passed in 0.49s` | pass |
| Fresh latest-run audit | `./.venv/bin/python - <<'PY' ... select(RunRow).order_by(created_at desc) ... PY` | 最新真实 run 为 `done` 且含非空 trace/report | `run_6a638169c5c44fe28f02880d373d17ce`, `status=done`, `trace_count=19`, `has_report=True` | pass |
| Fresh API read-path verification | `./.venv/bin/python - <<'PY' ... TestClient(create_app()) ... PY` | 读取接口全部 200 | `/v1/runs/{id}`、`/trace`、`/report.md` 均返回 200 | pass |
| Fresh trace coverage audit | `./.venv/bin/python - <<'PY' ... repo.list_tool_traces(latest_run) ... PY` | trace 覆盖四阶段 | `agents=['critic', 'planner', 'retrieval', 'review']` | pass |
| Git push after live-run fixes | `git push origin main` | 最新提交推送成功 | `1d9ac45..67eb498  main -> main` | pass |
| Phase 6 focused tests | `./.venv/bin/pytest tests/unit/test_cache_repository.py tests/unit/test_cached_connectors.py tests/integration/test_coordinator_degradation.py tests/integration/test_agent_runner.py tests/integration/test_tool_trace_recording.py -v` | 新增缓存/降级/trace 测试通过 | `9 passed in 0.27s` | pass |
| Full pytest after Phase 6 changes | `./.venv/bin/pytest -v` | 全量测试通过 | `34 passed in 0.57s` | pass |
| Fresh real-run trace audit after Phase 6 | `./.venv/bin/python - <<'PY' ... latest run + traces ... PY` | 最新真实 run 至少推进并写入新版 trace | `run_13693266052340eaab98cfe1ed69a82a`, `status=reviewing`, `trace_count=12`, `request_id` visible | pass |
| Fresh real-run completion after Phase 6 | `./.venv/bin/python - <<'PY' ... latest run + traces ... PY` | 最新真实 run 完成到 `done` | `run_13693266052340eaab98cfe1ed69a82a`, `status=done`, `trace_count=19` | pass |
| Fresh token-usage real-run audit | `./.venv/bin/python - <<'PY' ... latest run + nonzero token traces ... PY` | 真实 trace 出现非零 token usage | `run_07bb6d6f867a42db99fcec9c5e3b83bb`, retrieval traces show `input_tokens=772`, `output_tokens=244` | pass |
| Repository duplicate ID red-green | `./.venv/bin/pytest tests/unit/test_repository.py -v` | 允许不同 run 复用 `EV001` / `cluster_1` 这类业务 ID | 修复后 `6 passed in 0.23s` | pass |
| Real API round-trip live test | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` | 真实 `POST /v1/runs` 与 `GET` / `/trace` / `/report.md` 全链路通过 | `1 passed in 178.48s` | pass |
| Full pytest with live API | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` | 含 live test 的完整测试套件通过 | `41 passed in 156.79s` | pass |
| Stage summary + review batch focused tests | `./.venv/bin/pytest tests/unit/test_stage_summaries.py tests/unit/test_review_batches.py tests/unit/test_repository.py tests/integration/test_coordinator.py -v` | 新增阶段摘要和批次 review 测试通过 | `10 passed in 0.23s` | pass |
| Hypothesis repair unit test | `./.venv/bin/pytest tests/unit/test_workspace_tools.py -v` | 缺失 `counterevidence_ids` 时按 conflict clusters 自动补齐 | `1 passed in 0.23s` | pass |
| Fresh live API after planner repair | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` | 真实 planner 不再因缺失 `counterevidence_ids` 导致整 run 失败 | `1 passed in 173.55s` | pass |
| Full pytest with live API after Phase 7 | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` | 阶段摘要、batched review 与真实 API 一起通过 | `45 passed in 186.22s` | pass |
| Retrieval recovery focused tests | `./.venv/bin/pytest tests/unit/test_retrieval_recovery.py tests/integration/test_stage_degradation_status.py tests/integration/test_coordinator.py tests/integration/test_coordinator_degradation.py -v` | retrieval broaden retry 与 degraded stage summary 正确 | `6 passed in 0.27s` | pass |
| Full pytest after Phase 8 | `./.venv/bin/pytest -v` | retrieval recovery 改动未破坏默认路径 | `47 passed, 1 skipped in 0.63s` | pass |
| Fresh live API after retrieval recovery | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` | retrieval broaden retry 改动未破坏真实路径 | `1 passed in 206.52s` | pass |
| Full pytest with live API after Phase 8 | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` | retrieval recovery 与真实 API 一起通过 | `48 passed in 236.87s` | pass |
| Structured output recovery focused tests | `./.venv/bin/pytest tests/integration/test_agent_runner.py -v` | 自动重试和 retry 后 repair parse 生效 | `4 passed in 0.05s` | pass |
| Full pytest after Phase 9 | `./.venv/bin/pytest -v` | structured output recovery 未破坏默认路径 | `49 passed, 1 skipped in 0.63s` | pass |
| Fresh live API after Phase 9 | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` | runner 级 retry/repair 未破坏真实路径 | `1 passed in 235.53s` | pass |
| Full pytest with live API after Phase 9 | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` | structured output recovery 与真实 API 一起通过 | `50 passed in 228.74s` | pass |
| Planner rerun focused tests | `./.venv/bin/pytest tests/integration/test_coordinator_degradation.py tests/integration/test_runs_api.py -v` | coordinator rerun 和 API rerun 正确 | `6 passed in 0.29s` | pass |
| Full pytest after Phase 10 | `./.venv/bin/pytest -v` | planner rerun 改动未破坏默认路径 | `51 passed, 1 skipped in 0.66s` | pass |
| Fresh live API after Phase 10 | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` | planner rerun 改动未破坏真实主流程 | `1 passed in 452.52s` | pass |
| Full pytest with live API after Phase 10 | `RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` | planner rerun 与真实 API 一起通过 | `52 passed in 296.65s` | pass |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-03-08 | `fatal: not a git repository (or any of the parent directories): .git` | 1 | 记录初始状态，后续初始化仓库 |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 10: Planner Rerun Recovery 已完成 |
| Where am I going? | 当前可以转向剩余 SPEC 项，例如更系统的 budget 面或 planner rerun 的真实故障回放验证 |
| What's the goal? | 从 SPEC 构建 HypoForge MVP，并把真实 API、阶段摘要、batched review、retrieval recovery、structured output recovery、planner rerun 都纳入可重复验证 |
| What have I learned? | planner 失败恢复最好作为显式能力暴露，而不是只停留在 partial result |
| What have I done? | 已完成工程搭建、真实 API round-trip、带 live 的全量验证、结构化 stage summaries、batched review、planner hypothesis repair、retrieval recovery、structured output recovery、planner rerun 和远程同步 |

## Session Note: 2026-03-09 03:07 +08
- 已进入 Phase 12 设计：准备把 SPEC 18.3 / 19.2 的可信性规则显式落到 hypothesis payload，而不是只放在 planner prompt。
- 当前计划先写 red tests，覆盖 degraded retrieval / review / critic 时 `save_hypotheses()` 的宿主侧补齐，以及 Markdown report 对 limitations / uncertainty 的渲染。

## Session Note: 2026-03-09 03:12 +08
- Phase 12 第一轮 red-green 已完成：`Hypothesis` 新增 `limitations` / `uncertainty_notes`，`WorkspaceTools.save_hypotheses()` 会按 retrieval low-evidence、review partial、critic 缺失自动补齐可信性说明，Markdown report 同步渲染这些字段。
- Focused verification：`./.venv/bin/pytest tests/unit/test_workspace_tools.py tests/unit/test_report_renderer.py -v` -> `3 passed in 0.15s`。

## Session Note: 2026-03-09 03:21 +08
- Phase 11 和 Phase 12 的 fresh verification 已完成。
- 本地全量：`./.venv/bin/pytest -v` -> `56 passed, 1 skipped in 0.59s`。
- 单独 live round-trip：`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` -> `1 passed in 215.29s`。
- 带 live 的全量：`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` -> `57 passed in 239.67s`。

## Session Note: 2026-03-09 03:28 +08
- 已进入 Phase 13：补齐 SPEC 16.3 中剩余的 `tool step budget` 收束逻辑。
- 当前计划先写 red tests，覆盖 retrieval budget 收束、review 提前停机、以及 critic/planner 因 budget note 被标成 `degraded`。

## Session Note: 2026-03-09 03:34 +08
- Phase 13 第一轮 red-green 已完成：`AgentRunner` 改为抛 `ToolStepBudgetExceededError`，retrieval/review/critic/planner 都已接入阶段级收束。
- Focused verification：`./.venv/bin/pytest tests/unit/test_retrieval_recovery.py tests/unit/test_review_batches.py tests/integration/test_stage_degradation_status.py -v` -> `8 passed in 0.22s`。

## Session Note: 2026-03-09 03:43 +08
- Phase 13 fresh verification 已完成。
- 本地全量：`./.venv/bin/pytest -v` -> `59 passed, 1 skipped in 0.70s`。
- 单独 live round-trip：`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` -> `1 passed in 179.16s`。
- 带 live 的全量：`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest -v` -> `60 passed in 293.01s`。

## Session Note: 2026-03-09 03:49 +08
- 已进入 Phase 14：补 5 个 golden topics live regression。
- 当前计划先抽取共享 helper，再增加参数化 golden suite，并跑一次显式 golden regression。

## Session Note: 2026-03-09 03:54 +08
- Phase 14 第一轮 red-green 已完成：新增共享 live regression helper、单 topic live test 复用、以及 5-topic 参数化 suite。
- Focused verification：`./.venv/bin/pytest tests/unit/test_live_regressions.py tests/live/test_real_runs_api.py tests/live/test_golden_topics_api.py -v` -> `1 passed, 6 skipped in 0.28s`。

## Session Note: 2026-03-09 11:05 +08
- 首次 golden regression 实跑：`RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -v` -> `3 passed, 2 failed in 1228.22s`。
- 两个失败 topic 都是 planner 入库边界问题：真实模型给出的第 3 个 hypothesis 缺少足够的 `supporting_evidence_ids`，当前 repair 逻辑尚未补这一类缺口。

## Session Note: 2026-03-09 11:29 +08
- 已完成 supporting-evidence repair 的 unit red-green：`./.venv/bin/pytest tests/unit/test_workspace_tools.py -v` -> `3 passed in 0.17s`。
- 失败的两个 golden topics targeted rerun 已通过：`RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -k 'solid-state-battery-electrolyte or CO2-reduction-catalyst-selectivity' -v` -> `2 passed, 3 deselected in 409.99s`。

## Session Note: 2026-03-09 11:47 +08
- 5-topic golden regression 全绿：`RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -v` -> `5 passed in 1089.48s`。

## Session Note: 2026-03-09 11:48 +08
- 默认全量再次确认：`./.venv/bin/pytest -v` -> `61 passed, 6 skipped in 0.74s`。

## Session Note: 2026-03-09 13:43 +08
- 已切入 Phase 15 前端设计探索：确认 `frontend-design` 与 impeccable 的命令型 skill 已安装，可直接作为设计约束使用。
- 当前代码库仍无前端基底，因此需要先锁定页面定位和框架方向，再进入实现。

## Session Note: 2026-03-09 13:45 +08
- 已获得前端关键定位：页面是“对外展示型 demo 产品页”，目标用户是研究人员。
- 设计方向因此偏向“研究工作流仪表盘 + 展示页混合体”，而不是普通市场化 landing page。

## Session Note: 2026-03-09 13:47 +08
- 用户进一步明确不要介绍型网页，而要直接可操作的界面。
- 前端方向已收敛为“研究工作台 dashboard”，后续设计会围绕 run 提交、阶段进度、trace、证据和 hypothesis 结果展开。

## Session Note: 2026-03-09 13:49 +08
- 用户确认第一版前端需要直接启动真实 run，并采用“多视图控制台”结构。
- 设计重点因此转向：`New Run / Runs / Trace / Report` 这类研究控制台导航，而不是单页式信息堆叠。

## Session Note: 2026-03-09 13:55 +08
- 用户进一步给出框架偏好：优先直接复用 `Kiranism/next-shadcn-dashboard-starter`，前端只做最小必要调整。
- 前端设计策略因此收敛为“复用现成 dashboard shell + 替换成 HypoForge 的研究工作流内容层”。

## Session Note: 2026-03-09 13:58 +08
- 用户确认前端可以配套补 `GET /v1/runs` 列表接口。
- 这使得 `Runs` 页面可以直接读取服务端真实运行历史，符合多视图控制台定位。

## Session Note: 2026-03-09 14:12 +08
- 用户再次要求严格按既定前端方案执行，不要在实现前偏离：
- 1. 采用 `Kiranism/next-shadcn-dashboard-starter` 作为壳子；
- 2. 主视图固定为 `New Run`、`Runs`、`Run Detail / Overview`、`Trace`、`Report`；
- 3. 保留 app shell/sidebar/shadcn primitives，替换默认首页、示例数据、导航结构和业务页面；
- 4. 视觉固定为浅色学术编辑台。
- 当前开始把该方案正式写入 `docs/plans/`，然后直接进入 TDD 实现。

## Session Note: 2026-03-09 14:18 +08
- Phase 16 第一轮 backend TDD 已开始。
- `GET /v1/runs` 的红阶段已确认：先在 `tests/integration/test_runs_api.py` 写了列表测试，初次运行因为 `RunSummary` 和列表路由缺失而失败。
- 随后已补最小实现：`RunSummary` / `RunSummaryBody`、`RunCoordinator.list_runs()`、`RunRepository.list_runs()`、`GET /v1/runs`。

## Session Note: 2026-03-09 14:21 +08
- CORS 的红绿也已完成：先在 `tests/integration/test_health_api.py` 写 preflight 测试，初次失败于 `create_app()` 还不接受 `settings` 且无 CORS middleware。
- 现已补 `frontend_allowed_origins` 配置和 FastAPI `CORSMiddleware`。
- Focused verification：`./.venv/bin/pytest tests/integration/test_runs_api.py tests/integration/test_health_api.py -v` -> `6 passed in 0.28s`。

## Session Note: 2026-03-09 14:29 +08
- 已把 `Kiranism/next-shadcn-dashboard-starter` 拷入 `frontend/`，开始做 auth-free 的 HypoForge 化改造。
- 先删掉了会进入路由树的 auth/about/privacy/terms/workspaces/product/kanban/billing/exclusive/overview 页面，避免前端仍保留明显的模板入口。

## Session Note: 2026-03-09 14:35 +08
- 已完成前端壳子的第一轮重写：
- 1. root 和 `/dashboard` 都跳到 `/dashboard/new-run`；
- 2. sidebar 只保留 `New Run` / `Runs`；
- 3. 默认主题改为浅色 `hypoforge`；
- 4. 字体改为 `Newsreader + IBM Plex Sans + IBM Plex Mono`；
- 5. `providers.tsx` 已移除 Clerk 包裹，`src/proxy.ts` 已删除。

## Session Note: 2026-03-09 14:39 +08
- 已完成前端 API client 与五个主视图：
- 1. `frontend/src/lib/hypoforge.ts`
- 2. `frontend/src/hooks/use-hypoforge.ts`
- 3. `New Run` / `Runs` / `Run Overview` / `Trace` / `Report`
- 当前实现使用 `NEXT_PUBLIC_API_BASE_URL` 直连 FastAPI。

## Session Note: 2026-03-09 14:41 +08
- 首轮前端校验暴露三类问题：
- 1. starter 的 TS 配置尾部残留错误字段；
- 2. `react-markdown` 尚未安装；
- 3. 另一版占位页面内容覆盖了五个 app route 文件。
- 上述问题已逐一修复，并重新让 `npx tsc --noEmit` 转绿。

## Session Note: 2026-03-09 14:43 +08
- 前端完整验证已完成：
- 1. `cd frontend && npx tsc --noEmit` -> pass
- 2. `cd frontend && npm run lint` -> pass
- 3. `cd frontend && npm run build` -> pass
- backend 契约验证也已再次通过：
- `./.venv/bin/pytest tests/unit/test_repository.py tests/integration/test_runs_api.py tests/integration/test_health_api.py -v` -> `13 passed in 0.50s`
- 非阻断提示：Next build 会打印 `baseline-browser-mapping` 版本过旧提醒，但不影响构建与路由生成。

## Session Note: 2026-03-09 14:49 +08
- 前后端本地联调 smoke 已完成：
- 1. 启动 `uvicorn hypoforge.api.app:create_app --factory --host 127.0.0.1 --port 8000`；
- 2. 启动 `cd frontend && npm run dev -- --hostname 127.0.0.1 --port 3000`；
- 3. `curl -I http://127.0.0.1:3000/` 返回 `307` 并指向 `/dashboard/new-run`；
- 4. `curl http://127.0.0.1:3000/dashboard/new-run` 返回标题 `HypoForge Console`；
- 5. `curl http://127.0.0.1:8000/v1/runs` 返回真实 run 列表 JSON；
- 6. 验证后已停止本地前后端 dev 进程。

## Session Note: 2026-03-09 15:27 +08
- 已提交并推送前端集成状态：`feat: add hypoforge frontend console`，commit `eda9ca9`。
- fresh 默认后端全量验证：`./.venv/bin/pytest -v` -> `65 passed, 6 skipped in 0.78s`。
- 真实 API 验证：`RUN_REAL_API_TESTS=1 ./.venv/bin/pytest tests/live/test_real_runs_api.py -v` -> `1 passed in 219.60s`。

## Session Note: 2026-03-09 15:45 +08
- 5-topic golden regression 首轮 fresh run 出现一个真实稳定性失败：
- `RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -v`
- 结果：`4 passed, 1 failed in 1071.57s`
- 失败 topic：`diffusion model preference optimization`
- 根因：live run 偶发只保存 `<12` 篇 selected papers，未满足 SPEC 回归门槛。

## Session Note: 2026-03-09 15:52 +08
- 已为 retrieval 增加宿主侧 candidate-pool backfill：
- 1. 模型 broadened retrieval 后若仍 under-select，则按 `dedupe + ranking` 从当前 candidate pool 自动补足到阈值；
- 2. focused test：`./.venv/bin/pytest tests/unit/test_retrieval_recovery.py -v` -> `4 passed in 0.22s`；
- 3. targeted rerun：`RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -k diffusion-model-preference-optimization -v` -> `1 passed, 4 deselected in 191.21s`。

## Session Note: 2026-03-09 16:09 +08
- golden regression 已重新 fresh 通过：
- `RUN_REAL_API_TESTS=1 RUN_GOLDEN_TOPIC_TESTS=1 ./.venv/bin/pytest tests/live/test_golden_topics_api.py -v`
- 结果：`5 passed in 1010.48s`

## Session Note: 2026-03-09 16:24 +08
- 浏览器级 UI 复查发现明显 overflow：
- 1. 折叠态 sidebar 文本没有隐藏，挤压在 icon rail 中；
- 2. 长 golden topic 按钮和底部提交区在窄宽度下缺少换行/堆叠；
- 3. right infobar 仍引用 `/SPEC.md` 和本地 docs，造成前端 404。

## Session Note: 2026-03-09 16:31 +08
- 已完成前端 overflow hardening，并重新验证：
- 1. 修正 `app-sidebar.tsx` 折叠态 `group-data` 选择器；
- 2. `golden-topic-launcher.tsx` 改为允许多行换行；
- 3. `new-run-form.tsx` 底部说明/按钮改为小屏堆叠；
- 4. `info-sidebar.tsx` 改成站内可用链接，去掉断链；
- 5. `cd frontend && npm run lint` -> pass；
- 6. `cd frontend && npm run build` -> pass；
- 7. Playwright 在 1024px / 768px 截图下复查，不再出现先前那种明显越界和文本冲出容器。

## Session Note: 2026-03-09 17:02 +08
- 用户继续指出浏览器右侧存在大面积空白。
- 已定位为 shell-level 占位：
- 1. `dashboard/layout.tsx` 常驻渲染 `InfoSidebar`；
- 2. `infobar.tsx` 在 desktop 模式会保留固定宽度轨道；
- 3. 这导致主内容虽然可伸缩，但始终被挤压，视觉上像“右边白着一大块”。
- 已完成修复：
- 1. 从 dashboard 全局布局移除 `InfoSidebar` / `InfobarProvider`；
- 2. `NewRunForm` 和 `RunOverview` 的双栏布局只在 `2xl` 才触发；
- 3. `npm run lint` -> pass；
- 4. `npm run build` -> pass；
- 5. Playwright 在 1440px 下复查，`/dashboard/new-run` 与 `/dashboard/runs` 都已由主内容铺满可用宽度，不再保留右侧空白槽位。

## Session Note: 2026-03-09 18:15 +08
- 已完成前端控制台的全面打磨第一轮：
- 1. 新增 `frontend/src/lib/hypoforge-display.ts`，把 stage summary 和 trace result 映射为可读字段；
- 2. `Runs` 页新增 archive summary cards，并重做为“档案视图”；历史错误信息会压缩成受控预览，不再撑破布局；
- 3. `Run Overview` 改为 stage summary editorial cards、dossier health、评分面板和更干净的 paper shortlist；
- 4. `Trace` 改为列表 + inspector 的研究审计面板，小屏堆叠、大屏可分栏；
- 5. `Report` 改为 narrative draft + hypothesis outline 双区结构，并加入 sharing guidance；
- 6. 中等桌面响应式已收束：`Runs` 在 1024px 走卡片流，`StageProgressBand` 在 1024px 为双列；
- 7. 验证结果：
- `cd frontend && npm run lint` -> pass
- `cd frontend && npm run build` -> pass
- Playwright 复查：
- `1440px`：`/dashboard/runs`、`/dashboard/runs/{id}`、`/trace`、`/report` 均正常
- `1024px`：`/dashboard/runs` 改走卡片流，`/dashboard/runs/{id}` 的阶段带改为双列，且页面 `scrollWidth == innerWidth`

## Session Note: 2026-03-09 18:28 +08
- 已继续修正“卡片没有填充完整屏幕”的问题：
- 1. 根因是多个页面外层统一写成 `max-w-[1680px]`，在超宽屏下会留下额外留白；
- 2. 已从 `new-run/page.tsx`、`runs/page.tsx`、`run-overview.tsx`、`trace-view.tsx`、`report-view.tsx` 去掉该上限；
- 3. `cd frontend && npm run lint` -> pass
- 4. `cd frontend && npm run build` -> pass
- 5. Playwright 在 `2048x1295` 下复查 `/dashboard/runs/{id}`：
- `main/content width = 2000px`
- `first card width = 1936px`
- `scrollWidth = 2048`

## Session Note: 2026-03-09 18:40 +08
- 已将“去掉 max-width”调整为真正的自适应宽度算法：
- 1. 在 `frontend/src/styles/globals.css` 新增 `.workspace-shell`；
- 2. 规则为 `min(100%, clamp(0px, calc(100vw - clamp(1.5rem, 3vw, 4.5rem)), 1980px))`，兼顾铺满、边距和超宽屏上限；
- 3. `new-run`、`runs`、`run-overview`、`trace-view`、`report-view` 全部改用该容器；
- 4. `cd frontend && npm run lint` -> pass
- 5. `cd frontend && npm run build` -> pass
- 6. Playwright 在 `2048x1295` 下复查：
- `content width = 1980px`
- `first card width = 1916px`
- `scrollWidth = 2048`
- 当前状态：无横向溢出，但已保留比满屏略收的可读边距。

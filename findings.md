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

## Resources
- SPEC: `/Users/ccy/Documents/KEY/HypoForge/SPEC.md`
- planning-with-files skill: `/Users/ccy/.codex/skills/planning-with-files/SKILL.md`
- brainstorming skill: `/Users/ccy/.codex/superpowers/skills/brainstorming/SKILL.md`
- test-driven-development skill: `/Users/ccy/.codex/superpowers/skills/test-driven-development/SKILL.md`
- design doc: `/Users/ccy/Documents/KEY/HypoForge/docs/plans/2026-03-08-hypoforge-design.md`
- implementation plan: `/Users/ccy/Documents/KEY/HypoForge/docs/plans/2026-03-08-hypoforge-mvp.md`

## Visual/Browser Findings
- 无

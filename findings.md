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

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 采用 Python 包式 `src/` 布局并拆分 app/domain/infrastructure/interfaces | 对应 SPEC 的 API、Coordinator、Agent Runtime、Tool Host、Workspace Store 分层 |
| 先设计可替换 provider 抽象，再接 OpenAI/OpenAlex/S2 | 便于 TDD、离线测试与后续真 API 接入 |
| 以 SQLite 作为默认持久层 | 与 SPEC 一致，且适合 MVP |
| 默认远程仓库目标为 GitHub 私有仓库 `HypoForge` | 用户已确认按默认假设继续 |
| 使用 `.venv` + Python 3.12 作为本地执行环境 | 满足 SPEC 推荐版本并避开系统 Python 3.9 |
| 默认运行时接真实 provider/connector 边界，默认验证路径使用 fake services | 保持真实集成入口，同时避免本地验证依赖外部密钥和网络 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| 当前目录不是 Git 仓库 | 记录为待办，在实现完成后初始化并推送 |
| 远程仓库信息未知 | 需要在设计确认阶段明确或采用默认假设 |

## Resources
- SPEC: `/Users/ccy/Documents/KEY/HypoForge/SPEC.md`
- planning-with-files skill: `/Users/ccy/.codex/skills/planning-with-files/SKILL.md`
- brainstorming skill: `/Users/ccy/.codex/superpowers/skills/brainstorming/SKILL.md`
- test-driven-development skill: `/Users/ccy/.codex/superpowers/skills/test-driven-development/SKILL.md`
- design doc: `/Users/ccy/Documents/KEY/HypoForge/docs/plans/2026-03-08-hypoforge-design.md`
- implementation plan: `/Users/ccy/Documents/KEY/HypoForge/docs/plans/2026-03-08-hypoforge-mvp.md`

## Visual/Browser Findings
- 无

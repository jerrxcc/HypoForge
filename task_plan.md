# Task Plan: Build HypoForge From SPEC

## Goal
根据 `SPEC.md` 从零搭建 HypoForge MVP：完成 FastAPI + 多 agent 后端工程骨架、核心运行链路、测试与文档，并初始化 Git 仓库后同步到远程仓库。

## Current Phase
Phase 3

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

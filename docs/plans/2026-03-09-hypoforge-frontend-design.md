# HypoForge Frontend Design

## Goal
在现有后端已可真实运行的前提下，为 HypoForge 增加一个可直接操作的前端工作台。它不是介绍页，也不是普通 SaaS admin，而是面向研究人员的对外 demo 控制台。

## Fixed Constraints
- 采用 `Kiranism/next-shadcn-dashboard-starter` 作为前端壳子，做最小必要调整。
- 不重造 dashboard framework。
- 页面必须能直接输入 `topic` 并启动真实 run。
- 页面必须可视化 `retrieval -> review -> critic -> planner` 四阶段。
- 默认浅色。
- 视觉方向为“学术编辑台”，不是工业控制台。
- `SPEC.md` 已明确“不做复杂前端”，所以第一版前端只消费 API，不反向重构后端编排。

## Approach
复用 starter 的：
- app shell
- sidebar
- shadcn 基础组件
- table / form / tabs / layout

替换 starter 的：
- 默认首页
- 示例数据
- 导航结构
- 所有业务页面
- status / stage / progress 可视化

轻改 starter 的：
- theme tokens
- typography
- stage progress 组件
- trace inspector 样式

## Information Architecture
第一版固定为 4 个主视图，外加一个 run 详情子视图：

1. `New Run`
- 输入 `topic`
- 设置约束
- 启动真实 run
- 显示 golden topics 快捷入口

2. `Runs`
- 调 `GET /v1/runs`
- 展示历史 run 列表
- 列里看 `status / topic / updated_at / selected papers / evidence / hypotheses`
- 点一行进入 run 详情

3. `Run Detail / Overview`
- 顶部四阶段进度带：`retrieval -> review -> critic -> planner`
- 展示 `stage_summaries`
- 展示 selected papers、evidence cards、conflict clusters、hypotheses 摘要
- 明确显示 degraded / failed 原因

4. `Trace`
- 左侧 trace 列表
- 右侧看 `tool_args / result_summary / latency / tokens / request_id / error`

5. `Report`
- 左侧 markdown report
- 右侧 hypothesis 导航和证据跳转

全局导航只保留：
- `New Run`
- `Runs`

run 详情内部再切：
- `Overview`
- `Trace`
- `Report`

## Route Shape
建议路由如下：

- `/` -> redirect to `/dashboard/new-run`
- `/dashboard/new-run`
- `/dashboard/runs`
- `/dashboard/runs/[runId]`
- `/dashboard/runs/[runId]/trace`
- `/dashboard/runs/[runId]/report`

## Look
视觉方向固定为：
- 默认浅色
- 学术编辑台，不是工业控制台
- 复用 starter 的布局，不复用它的默认 SaaS 味道
- 字体：`Newsreader + IBM Plex Sans`
- 色板：纸白、墨蓝灰、氧化青、赭红

### Visual Tokens
- Background: warm paper
- Foreground: ink blue-gray
- Accent: oxidized teal
- Conflict / failure: muted ochre-red
- Surfaces: layered off-white cards with subtle borders

### Layout Tone
- 左侧固定导航
- 中部主画布
- 右侧在 trace/report 等视图中作为 inspector 或 outline
- 不堆 KPI 卡片
- 让阶段流程带成为页面骨架

## Backend Additions
为了支持这一版前端，补 2 个最小后端扩展：

1. `GET /v1/runs`
2. 一个轻量的 run list schema，避免 `Runs` 页直接拿完整 `RunResult`

如本地联调需要，再补：
- CORS 支持

## Reuse Boundary in Practice
保留：
- `dashboard/layout`
- sidebar/header primitives
- shadcn 组件
- `@tanstack/react-table`
- `react-resizable-panels`

移除：
- Clerk auth gate
- workspaces/product/kanban/billing/exclusive 等示例页面
- 与 HypoForge 无关的 demo copy

## Acceptance Bar
这一版前端达标时，应满足：
- 能从浏览器直接启动真实 run
- 能查看 run 历史列表
- 能在详情里看到明确的四阶段进度和 stage summaries
- 能浏览 trace
- 能阅读 report
- 视觉上明显不是未修改的通用 SaaS admin 模板

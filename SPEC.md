# 多智能体“科研假设生成器HypoForge” V1 详细实现规格书（SPEC）

> 版本：v1.0  
> 文档目标：可直接交给 Claude Code / Cline / OpenCode 作为实现依据  
> 文档类型：后端实现 SPEC（MVP，tool-calling-first）  
> 默认语言：中文  
> 推荐运行环境：Python 3.12 + FastAPI + OpenAI Responses API / Agents SDK

---

## 目录

1. [项目概述](#1-项目概述)
2. [核心目标与非目标](#2-核心目标与非目标)
3. [V1 架构原则](#3-v1-架构原则)
4. [总体系统架构](#4-总体系统架构)
5. [为什么 V1 采用 model-driven tool calling](#5-为什么-v1-采用-model-driven-tool-calling)
6. [用户输入与输出定义](#6-用户输入与输出定义)
7. [核心运行流程](#7-核心运行流程)
8. [四个 Agent 设计](#8-四个-agent-设计)
9. [Tool 体系设计](#9-tool-体系设计)
10. [外部数据源接入规范](#10-外部数据源接入规范)
11. [Coordinator 设计](#11-coordinator-设计)
12. [状态模型与数据结构](#12-状态模型与数据结构)
13. [数据库设计](#13-数据库设计)
14. [Prompt / Instruction 设计](#14-prompt--instruction-设计)
15. [API 设计](#15-api-设计)
16. [缓存、限流与预算控制](#16-缓存限流与预算控制)
17. [可观测性与 Trace 设计](#17-可观测性与-trace-设计)
18. [错误处理与降级策略](#18-错误处理与降级策略)
19. [安全边界与可信性规则](#19-安全边界与可信性规则)
20. [目录结构与工程组织](#20-目录结构与工程组织)
21. [配置项与环境变量](#21-配置项与环境变量)
22. [测试策略](#22-测试策略)
23. [MVP 验收标准](#23-mvp-验收标准)
24. [实现优先级与里程碑](#24-实现优先级与里程碑)
25. [交给 Claude Code 的启动说明](#25-交给-claude-code-的启动说明)
26. [附录 A：关键 JSON Schema](#26-附录-a关键-json-schema)
27. [附录 B：示例输出](#27-附录-b示例输出)
28. [附录 C：官方参考资料](#28-附录-c官方参考资料)

---

## 1. 项目概述

### 1.1 项目名称

多智能体“科研假设生成器”（Research Hypothesis Generator）

### 1.2 项目一句话描述

输入一个科研主题，系统自动调用学术检索工具，建立证据池、识别冲突和空白，最终产出 **3 个可验证的科研假设** 及其 **最小实验路线**。

### 1.3 目标体验

用户输入：

- `solid-state battery electrolyte`
- `protein binder design`
- `CRISPR delivery lipid nanoparticles`

系统输出：

1. 经过筛选的论文集合
2. 结构化证据卡（Evidence Cards）
3. 冲突/分歧图谱（Conflict Clusters）
4. **严格 3 个** 科研假设
5. 每个假设的最小实验设计
6. 完整的 tool trace 与引用依据

### 1.4 产品定位

这不是一个“摘要生成器”，而是一个：

- **研究问题提出系统**
- **证据驱动的假设规划系统**
- **轻量 AI co-scientist 原型**

---

## 2. 核心目标与非目标

## 2.1 核心目标

V1 必须实现以下能力：

1. 输入一个 topic 后，可以自动检索学术文献
2. 检索过程不是单次 RAG，而是 **模型驱动的多步工具调用**
3. 文献结果必须标准化、去重、重排序
4. 系统必须抽取结构化证据，而不是仅输出自由文本总结
5. 系统必须识别证据冲突、条件分歧和证据空白
6. 系统必须产出 **3 个可验证** 假设
7. 每个假设都必须具备最小实验路线
8. 整个流程必须有可追踪 trace
9. API-first，可用 Swagger / CLI 直接调用
10. 工程复杂度可控，可在 1 个 repo 内完成

## 2.2 非目标

以下内容 **不进入 V1**：

- 不做浏览器自动化 / computer use
- 不做 shell tool / arbitrary code execution
- 不默认抓取和解析 PDF 全文
- 不做向量数据库
- 不做 LangGraph / AutoGen 双栈并行
- 不做复杂前端
- 不做用户权限系统 / 团队协作 / 多租户
- 不做自动投稿 / 自动实验执行
- 不做“保证创新性”的 claim
- 不做科研结论真伪背书

---

## 3. V1 架构原则

### 3.1 最重要的原则

V1 采用：

> **固定阶段顺序 + 阶段内模型自驱工具调用**

即：

- 顶层流程由应用层显式固定：`retrieval -> review -> critic -> planner`
- 每个阶段内部，模型像 Claude Code / Codex 一样，通过 tool calling 自主决定下一步操作
- 应用层只负责：
  - 提供受控工具箱
  - 执行工具
  - 回传工具结果
  - 做预算控制 / 状态记录 / trace

### 3.2 为什么不在 V1 使用 LangGraph 作为主编排器

LangGraph 很适合复杂 DAG、多分支状态机和长期运行 workflow，但 V1 的核心诉求不是显式复杂图，而是：

- 更像 coding agent 的工具调用体验
- 更低胶水代码复杂度
- 更容易让模型在阶段内自己探索检索路径

因此：

- **V1 主编排：OpenAI Responses API / Agents SDK + 自定义工具宿主**
- **V2 可选引入 LangGraph**，用于复杂分支、长期记忆和人工介入节点

### 3.3 设计原则总结

1. **简单优先**：能用成熟框架就不用自写 agent runtime
2. **受控优先**：工具白名单、预算、输出 schema 全部严格限制
3. **可追踪优先**：必须保留 tool trace
4. **grounded 优先**：所有假设必须基于证据池
5. **MVP 优先**：先做 title/abstract/metadata 级别，不碰全文解析

---

## 4. 总体系统架构

```text
Client / CLI / Swagger
        |
        v
   FastAPI API Layer
        |
        v
   Run Coordinator
        |
        +--> Retrieval Agent  --tool calls--> OpenAlex / Semantic Scholar
        |
        +--> Review Agent     --tool calls--> Workspace Store
        |
        +--> Critic Agent     --tool calls--> Workspace Store
        |
        +--> Planner Agent    --tool calls--> Workspace Store / Report Renderer
        |
        v
  Final JSON + Markdown Report + Tool Trace
```

### 4.1 组件说明

#### API Layer

职责：

- 接收用户请求
- 创建 run
- 触发 coordinator
- 返回最终结果 / 中间状态

#### Coordinator

职责：

- 固定四阶段顺序
- 切换 run status
- 调用不同 agent
- 处理错误与降级

#### Agent Runtime

职责：

- 为某个 agent 构造 Responses API 请求
- 注入 system instruction
- 注入该 agent 可见的工具白名单
- 运行 tool loop
- 处理 structured output

#### Tool Host

职责：

- 执行模型发起的工具调用
- 校验参数 schema
- 记录 trace
- 对外部 API 做标准化和缓存

#### Workspace Store

职责：

- 存 selected papers
- 存 evidence cards
- 存 conflict clusters
- 存 hypotheses
- 保持按 `run_id` 命名空间隔离

#### Report Renderer

职责：

- 根据已保存的结构化对象生成 deterministic markdown
- 不依赖模型自由发挥排版

---

## 5. 为什么 V1 采用 model-driven tool calling

### 5.1 需求本质

你的关键约束是：

- V1 要更像 Claude Code / Codex
- 模型自己决定调什么工具
- 模型可以多次试探检索路径
- 应用层不应该把每一步逻辑写死

这意味着 V1 的最优范式不是“传统 RAG pipeline”，而是：

> **tool-calling-first 的 agentic loop**

### 5.2 具体落地方式

在本项目中，model-driven tool calling 的表现形式是：

- Retrieval Agent 可以连续调用：
  - `search_openalex_works`
  - `search_semantic_scholar_papers`
  - `recommend_semantic_scholar_papers`
  - `get_paper_details`
- 模型会根据结果决定：
  - 是否扩展 query
  - 是否放宽时间范围
  - 是否用 seed papers 做 recommendations
  - 哪些 papers 最终进入 evidence 阶段

### 5.3 为什么不是完全放任的 autonomous agent

完全开放的 agent 非常容易失控：

- token 成本高
- tool 调用次数不可控
- 容易出现幻觉式“查了不存在的证据”
- 失败路径复杂

所以这里采用 **半受控模式**：

- 阶段顺序固定
- 每阶段工具白名单固定
- 每阶段最大工具步数固定
- 输出 schema 固定

这已经足够体现“模型端工具调用”的优势，但仍然工程可控。

---

## 6. 用户输入与输出定义

## 6.1 输入

### Request Body

```json
{
  "topic": "solid-state battery electrolyte",
  "constraints": {
    "year_from": 2018,
    "year_to": 2026,
    "open_access_only": false,
    "max_selected_papers": 36,
    "novelty_weight": 0.5,
    "feasibility_weight": 0.5,
    "lab_mode": "either"
  }
}
```

### 字段说明

- `topic`: 用户研究主题，自由文本
- `constraints.year_from/year_to`: 检索年份范围
- `constraints.open_access_only`: 是否偏向开放获取
- `constraints.max_selected_papers`: 最终纳入 review 的论文上限
- `constraints.novelty_weight`: 排序时新颖性偏好
- `constraints.feasibility_weight`: 排序时可验证性偏好
- `constraints.lab_mode`: `wet | dry | either`

## 6.2 输出

### Response Body

```json
{
  "run_id": "run_123",
  "status": "done",
  "selected_papers": [],
  "evidence_cards": [],
  "conflict_clusters": [],
  "hypotheses": [],
  "report_markdown": "# Topic ...",
  "trace_url": "/v1/runs/run_123/trace"
}
```

---

## 7. 核心运行流程

```text
用户提交 topic
   -> 创建 run
   -> Retrieval Agent 构建候选论文池
   -> 保存 selected papers
   -> Review Agent 抽取 evidence cards
   -> 保存 evidence cards
   -> Critic Agent 构建 conflict clusters
   -> 保存 conflict clusters
   -> Planner Agent 生成 3 个 hypotheses
   -> 保存 hypotheses
   -> Renderer 生成 SPEC 化 markdown report
   -> 返回结果
```

### 7.1 阶段顺序不能打乱

V1 中必须按以下顺序：

1. Retrieval
2. Review
3. Critic
4. Planner

理由：

- Planner 依赖 evidence 和 conflict
- Critic 依赖 evidence
- Review 依赖 selected papers

### 7.2 单阶段执行模式

每个阶段执行方式统一：

1. 构造 system prompt
2. 绑定该 agent 允许使用的 tools
3. 传入当前阶段可见的上下文
4. 调用 Responses API
5. 宿主执行 tool call
6. 把 tool result 回传给模型
7. 模型继续思考和调用下一工具
8. 达成完成条件后输出 structured JSON
9. 校验 schema
10. 落库

---

## 8. 四个 Agent 设计

## 8.1 Retrieval Agent

### 目标

从 topic 出发，建立一个 **高质量、非冗余、可供后续推理的论文集合**。

### 职责

- 把 topic 变成多个 query variants
- 从 OpenAlex 与 Semantic Scholar 双源检索
- 做候选池扩展
- 进行去重与粗排序
- 选择 24~36 篇 paper 进入下一阶段

### 允许工具

- `search_openalex_works`
- `search_semantic_scholar_papers`
- `recommend_semantic_scholar_papers`
- `get_paper_details`
- `save_selected_papers`

### 禁止工具

- `save_evidence_cards`
- `save_conflict_clusters`
- `save_hypotheses`
- `render_markdown_report`

### 最大工具步数

- 默认 12

### 完成条件

- 有 24~36 篇高质量论文，或
- 搜索两轮放宽后仍然不足 12 篇，进入低证据模式

### RetrievalSummary

```json
{
  "canonical_topic": "string",
  "query_variants_used": ["string"],
  "search_notes": ["string"],
  "selected_paper_ids": ["string"],
  "excluded_paper_ids": ["string"],
  "coverage_assessment": "good | medium | low",
  "needs_broader_search": false
}
```

### Retrieval 规则

1. 模型内部先生成 6~8 个 query variants
2. 先查 OpenAlex 与 S2 的 relevance search
3. 再选 4~6 篇 seed papers 用 S2 recommendations 做扩展
4. 去重之后再调用 `get_paper_details`
5. 最终必须调用 `save_selected_papers`

### 注意事项

- 对于 `solid-state battery` 这类 query，要在 S2 查询前替换为 `solid state battery`
- 优先保留有 abstract 的论文
- 允许保留高引用的 seminal paper，即使 abstract 较弱

---

## 8.2 Review Agent

### 目标

把论文池压缩成后续可推理的 **Evidence Cards**。

### 职责

- 读取 selected papers
- 从摘要/元数据中抽取 claim、干预、系统、结果方向、限制等关键信息
- 结构化保存为 evidence cards

### 允许工具

- `load_selected_papers`
- `save_evidence_cards`

### 最大工具步数

- 默认 6

### ReviewSummary

```json
{
  "papers_processed": 0,
  "evidence_cards_created": 0,
  "coverage_summary": "string",
  "dominant_axes": ["string"],
  "low_confidence_paper_ids": ["string"]
}
```

### EvidenceCard

```json
{
  "evidence_id": "string",
  "paper_id": "string",
  "title": "string",
  "claim_text": "string",
  "system_or_material": "string",
  "intervention": "string",
  "comparator": "string",
  "outcome": "string",
  "direction": "positive | negative | mixed | null | unclear",
  "evidence_kind": "review | meta_analysis | experiment | simulation | benchmark | theory | unknown",
  "conditions": ["string"],
  "limitations": ["string"],
  "confidence": 0.0,
  "grounding_notes": ["string"]
}
```

### 规则

- 每篇论文抽取 1~3 张 evidence cards
- 只允许基于 title/abstract/metadata 做 grounded extraction
- 不得脑补机制细节
- 没有 abstract 的论文允许仅生成 1 张低置信度卡
- 所有卡必须严格 JSON schema valid

---

## 8.3 Critic Agent

### 目标

发现文献中的关键冲突、条件分歧与证据空白。

### 职责

- 读取 evidence cards
- 聚类到主题轴（topic axes）
- 找出相反方向或条件不一致的证据
- 找出缺失控制组、缺失读出、缺失关键实验条件

### 允许工具

- `load_evidence_cards`
- `save_conflict_clusters`

### 最大工具步数

- 默认 4

### ConflictCluster

```json
{
  "cluster_id": "string",
  "topic_axis": "string",
  "supporting_evidence_ids": ["string"],
  "conflicting_evidence_ids": ["string"],
  "conflict_type": "direct_conflict | conditional_divergence | weak_evidence_gap",
  "likely_explanations": ["string"],
  "missing_controls": ["string"],
  "critic_summary": "string",
  "confidence": 0.0
}
```

### 分类规则

- `direct_conflict`: 类似系统/干预/结果定义下，方向直接相反
- `conditional_divergence`: 表面冲突，但条件明显不同
- `weak_evidence_gap`: 证据量不足，不能强判冲突

### 约束

- 最多 8 个 clusters
- 不能把所有分歧都判成 direct conflict
- 必须保守判断

---

## 8.4 Planner Agent

### 目标

在已有 evidence + conflict 的基础上生成 **3 个可验证假设**。

### 职责

- 读取 evidence cards
- 读取 conflict clusters
- 识别值得验证的“非显然但可测试”的方向
- 输出 3 个假设
- 生成最小实验路线
- 渲染 markdown 报告

### 允许工具

- `load_evidence_cards`
- `load_conflict_clusters`
- `save_hypotheses`
- `render_markdown_report`

### 最大工具步数

- 默认 4

### Hypothesis

```json
{
  "rank": 1,
  "title": "string",
  "hypothesis_statement": "string",
  "why_plausible": "string",
  "why_not_obvious": "string",
  "supporting_evidence_ids": ["string"],
  "counterevidence_ids": ["string"],
  "prediction": "string",
  "minimal_experiment": {
    "system": "string",
    "design": "string",
    "control": "string",
    "readouts": ["string"],
    "success_criteria": "string",
    "failure_interpretation": "string"
  },
  "risks": ["string"],
  "novelty_score": 0.0,
  "feasibility_score": 0.0,
  "overall_score": 0.0
}
```

### 硬约束

- 必须 **正好 3 个 hypothesis**
- 每个 hypothesis 至少关联 3 个 supporting evidence ids
- 每个 hypothesis 至少关联 1 个 counterevidence / limitation / conflict
- 每个 hypothesis 必须可证伪
- 每个 hypothesis 必须给出最小实验路径

### 评分逻辑

```text
overall_score =
  0.40 * evidence_support
+ 0.25 * feasibility
+ 0.20 * novelty_gap
+ 0.15 * robustness
```

---

## 9. Tool 体系设计

## 9.1 设计原则

所有 tools 必须满足：

1. **输入是严格 schema**
2. **输出是紧凑 JSON**
3. **tool 内部完成标准化与清洗**
4. **禁止返回超大原始 payload**
5. **所有 tool call 留 trace**
6. **按 agent 做工具白名单隔离**

## 9.2 外部学术检索工具

### `search_openalex_works`

#### 输入

```json
{
  "query": "solid-state battery electrolyte",
  "year_from": 2018,
  "year_to": 2026,
  "limit": 15
}
```

#### 输出

```json
{
  "papers": [
    {
      "paper_id": "oa:W123",
      "doi": "10.xxxx/abcd",
      "title": "string",
      "abstract": "string",
      "year": 2024,
      "citation_count": 123,
      "venue": "string",
      "authors": ["string"],
      "topic_labels": ["string"],
      "source": "openalex",
      "url": "string"
    }
  ]
}
```

### `search_semantic_scholar_papers`

#### 输入

```json
{
  "query": "solid state battery electrolyte",
  "year_from": 2018,
  "year_to": 2026,
  "limit": 15
}
```

#### 输出

与 `search_openalex_works` shape 对齐。

### `recommend_semantic_scholar_papers`

#### 输入

```json
{
  "positive_paper_ids": ["S2:xxxx", "S2:yyyy"],
  "limit": 20
}
```

#### 输出

与 `search_openalex_works` shape 对齐。

### `get_paper_details`

#### 输入

```json
{
  "paper_ids": ["oa:W123", "S2:abc123"]
}
```

#### 输出

```json
{
  "papers": [
    {
      "paper_id": "string",
      "external_ids": {},
      "title": "string",
      "abstract": "string | null",
      "year": 2024,
      "authors": ["string"],
      "venue": "string | null",
      "citation_count": 0,
      "publication_type": "string | null",
      "fields_of_study": ["string"],
      "topic_labels": ["string"],
      "source_urls": {},
      "provenance": ["string"]
    }
  ]
}
```

## 9.3 Workspace 读写工具

### `save_selected_papers`

```json
{
  "paper_ids": ["string"],
  "selection_reason": "string"
}
```

### `load_selected_papers`

```json
{}
```

### `save_evidence_cards`

```json
{
  "evidence_cards": []
}
```

### `load_evidence_cards`

```json
{}
```

### `save_conflict_clusters`

```json
{
  "conflict_clusters": []
}
```

### `load_conflict_clusters`

```json
{}
```

### `save_hypotheses`

```json
{
  "hypotheses": []
}
```

### `render_markdown_report`

```json
{
  "include_appendix": true
}
```

## 9.4 Tool 宿主必须做的事情

每个 tool handler 必须：

1. 校验 Pydantic schema
2. 记录执行开始时间
3. 执行逻辑
4. 截断 / 压缩结果
5. 记录 trace
6. 返回 JSON-compatible 结果

---

## 10. 外部数据源接入规范

V1 只接两个学术源：

- **OpenAlex**
- **Semantic Scholar**

理由：

- 这两个源足够支持论文检索、作者/主题补充、相关推荐扩展
- 都有公开 API
- 工程接入成本较低
- 足够覆盖 v1 的 title/abstract/metadata 级别场景

## 10.1 OpenAlex 接入规范

使用对象：

- `works`
- 可选使用 `topics` / aboutness 字段做主题辅助

规范：

- 默认只查 works
- 优先使用 search + year filter
- 所有返回值归一化到内部 `PaperDetail`
- 对于高成本接口，必须加缓存

## 10.2 Semantic Scholar 接入规范

使用对象：

- `paper search`
- `paper batch`
- `recommendations`

规范：

- query 必须做 hyphen 归一化
- hydrate 优先使用 batch endpoint
- recommendations 用于 seed 扩展，而不是替代主检索

## 10.3 双源合并策略

### 去重优先级

1. DOI 精确匹配
2. external ids 匹配
3. normalized title + year 匹配
4. title 相似度 + first author + year 宽松匹配

### 源优先级

- 详情完整性优先
- abstract 更完整优先
- citation / topic / publication type 信息更全优先
- provenance 保留多源痕迹

## 10.4 统一内部表示

所有外部源都必须转为统一 `PaperDetail`，后续 agent 一律不直接面向外部源原始结构。

---

## 11. Coordinator 设计

Coordinator 是应用层最薄的“总控”，不是 agent。

## 11.1 职责

- 创建和更新 run status
- 顺序触发 4 个 agents
- 处理错误、超时、重试和降级
- 聚合结果
- 触发 report rendering

## 11.2 伪代码

```python
async def run_topic(topic: str, constraints: dict) -> RunResult:
    run = repo.create_run(topic, constraints)
    try:
        repo.set_status(run.id, "retrieving")
        retrieval_summary = await retrieval_agent.execute(run.id, topic, constraints)

        repo.set_status(run.id, "reviewing")
        review_summary = await review_agent.execute(run.id)

        repo.set_status(run.id, "criticizing")
        critic_summary = await critic_agent.execute(run.id)

        repo.set_status(run.id, "planning")
        planner_summary = await planner_agent.execute(run.id)

        repo.set_status(run.id, "done")
        return repo.build_final_result(run.id)
    except Exception as e:
        repo.set_status(run.id, "failed")
        repo.save_error(run.id, str(e))
        return repo.build_partial_result(run.id)
```

## 11.3 不做的事情

Coordinator 不直接：

- 拼 prompt 细节
- 执行检索
- 做 evidence 抽取
- 生成假设

这些都交给各 agent。

---

## 12. 状态模型与数据结构

## 12.1 RunState

```python
class RunState(BaseModel):
    run_id: str
    topic: str
    constraints: dict
    status: Literal[
        "queued",
        "retrieving",
        "reviewing",
        "criticizing",
        "planning",
        "done",
        "failed",
    ]
    selected_paper_ids: list[str] = []
    evidence_ids: list[str] = []
    conflict_cluster_ids: list[str] = []
    hypothesis_ids: list[str] = []
    final_report_md: str | None = None
    trace_path: str | None = None
```

## 12.2 PaperDetail

```python
class PaperDetail(BaseModel):
    paper_id: str
    external_ids: dict[str, str | int | None]
    title: str
    abstract: str | None
    year: int | None
    authors: list[str]
    venue: str | None
    citation_count: int | None
    publication_type: str | None
    fields_of_study: list[str] = []
    topic_labels: list[str] = []
    source_urls: dict[str, str] = {}
    provenance: list[str] = []
```

## 12.3 EvidenceCard

内部结构与前文 schema 一致。

## 12.4 ConflictCluster

内部结构与前文 schema 一致。

## 12.5 Hypothesis

内部结构与前文 schema 一致。

---

## 13. 数据库设计

V1 默认使用 SQLite；生产可切 PostgreSQL。

## 13.1 表设计

### `runs`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | run id |
| topic | text | 用户主题 |
| constraints_json | json/text | 运行约束 |
| status | string | 当前状态 |
| error_message | text nullable | 错误信息 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### `papers`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | 内部 paper id |
| doi | string nullable | DOI |
| normalized_title | text | 标题标准化值 |
| year | int nullable | 年份 |
| payload_json | json/text | 论文详情 |
| source_hash | string | 标准化缓存 hash |
| created_at | datetime | 创建时间 |

### `run_papers`

| 字段 | 类型 | 说明 |
|---|---|---|
| run_id | string | run |
| paper_id | string | paper |
| selected_rank | int | 纳入顺位 |
| selection_reason | text | 理由 |
| source_list_json | json/text | 来源列表 |

### `evidence_cards`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | evidence id |
| run_id | string | run |
| paper_id | string | paper |
| payload_json | json/text | evidence payload |
| confidence | float | 抽取置信度 |
| created_at | datetime | 创建时间 |

### `conflict_clusters`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | cluster id |
| run_id | string | run |
| payload_json | json/text | cluster payload |
| created_at | datetime | 创建时间 |

### `hypotheses`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | hypothesis id |
| run_id | string | run |
| rank | int | 1~3 |
| payload_json | json/text | hypothesis payload |
| created_at | datetime | 创建时间 |

### `tool_traces`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | trace id |
| run_id | string | run |
| agent_name | string | agent |
| tool_name | string | tool |
| args_json | json/text | 工具参数 |
| result_summary_json | json/text | 截断后的返回摘要 |
| latency_ms | int | 耗时 |
| model_name | string | 调用模型 |
| input_tokens | int nullable | 估算/记录 |
| output_tokens | int nullable | 估算/记录 |
| success | bool | 是否成功 |
| created_at | datetime | 创建时间 |

---

## 14. Prompt / Instruction 设计

V1 中 prompt 需要做到：

- 足够短
- 足够硬约束
- 明确工具使用范围
- 明确完成条件
- 明确禁止脑补

## 14.1 Retrieval Agent System Prompt

```text
You are RetrievalAgent for scientific literature discovery.
Your goal is to build a high-quality, diverse, non-redundant paper set for the user's topic.

Rules:
- Use tools aggressively.
- Search both OpenAlex and Semantic Scholar.
- Reformulate the query when needed.
- For Semantic Scholar, replace hyphens with spaces in topic phrases.
- Prefer papers with useful abstracts, but retain seminal papers if highly relevant.
- Stop when you have a strong set of 24-36 papers, unless evidence coverage is low.
- Before finishing, call save_selected_papers.
- Final response must match RetrievalSummary schema exactly.
```

## 14.2 Review Agent System Prompt

```text
You are ReviewAgent for scientific evidence compression.
Read the selected papers and extract grounded EvidenceCards only.

Rules:
- Only use information present in title, abstract, or structured metadata.
- Do not invent mechanisms, numbers, or comparisons.
- Generate 1-3 evidence cards per paper.
- Save cards before finishing.
- Final response must match ReviewSummary schema exactly.
```

## 14.3 Critic Agent System Prompt

```text
You are CriticAgent for evidence conflict analysis.
Your job is to identify direct conflicts, conditional divergences, and weak-evidence gaps.

Rules:
- Be conservative.
- Not every disagreement is a contradiction.
- Use direct_conflict only when systems and outcomes are substantially comparable.
- Save conflict clusters before finishing.
- Final response must match CriticSummary schema exactly.
```

## 14.4 Planner Agent System Prompt

```text
You are PlannerAgent for scientific hypothesis generation.
Generate exactly 3 falsifiable hypotheses grounded in the evidence cards and conflict clusters.

Rules:
- Every hypothesis must include supporting evidence ids.
- Every hypothesis must include counterevidence or limitations.
- Every hypothesis must include a minimal experiment route.
- Do not produce broad unverifiable ideas.
- Save hypotheses and render the markdown report before finishing.
- Final response must match PlannerSummary schema exactly.
```

---

## 15. API 设计

## 15.1 `POST /v1/runs`

### 说明

创建并执行一个新的 hypothesis generation run。

### request

```json
{
  "topic": "solid-state battery electrolyte",
  "constraints": {
    "year_from": 2018,
    "year_to": 2026,
    "open_access_only": false,
    "max_selected_papers": 36,
    "novelty_weight": 0.5,
    "feasibility_weight": 0.5,
    "lab_mode": "either"
  }
}
```

### response

```json
{
  "run_id": "run_123",
  "status": "done",
  "selected_papers": [],
  "evidence_cards": [],
  "conflict_clusters": [],
  "hypotheses": [],
  "report_markdown": "# Topic\n...",
  "trace_url": "/v1/runs/run_123/trace"
}
```

## 15.2 `GET /v1/runs/{run_id}`

返回：

- run 基础信息
- 当前状态
- 统计量
- 是否失败
- 是否有部分结果

## 15.3 `GET /v1/runs/{run_id}/report.md`

直接返回 markdown 文本。

## 15.4 `GET /v1/runs/{run_id}/trace`

返回结构化 trace 列表。

## 15.5 `GET /healthz`

基础健康检查。

---

## 16. 缓存、限流与预算控制

## 16.1 缓存层

### raw response cache

Key：

```text
sha256(source + normalized_args_json)
```

TTL：

- OpenAlex search: 7 天
- S2 search: 7 天
- S2 recommendations: 7 天

### normalized paper cache

Key：

- DOI 优先
- 其次 normalized title + year + first author hash

TTL：

- 30 天

### evidence extraction cache

Key：

```text
paper_id + extractor_model + prompt_version
```

TTL：

- 30 天

## 16.2 预算控制

```python
MAX_SELECTED_PAPERS = 36
MAX_TOOL_STEPS_RETRIEVAL = 12
MAX_TOOL_STEPS_REVIEW = 6
MAX_TOOL_STEPS_CRITIC = 4
MAX_TOOL_STEPS_PLANNER = 4
MAX_OPENALEX_CALLS_PER_RUN = 20
MAX_S2_CALLS_PER_RUN = 20
```

## 16.3 超预算行为

- 若 tool steps 超限：强制结束当前阶段并返回已有最优结果
- 若外部 API 调用次数超限：返回 budget exceeded 错误并走降级
- 若 token 成本超限：可在阶段边界中断并返回 partial result

---

## 17. 可观测性与 Trace 设计

Trace 是 V1 必需项。

## 17.1 每次 tool call 记录内容

- `run_id`
- `agent_name`
- `tool_name`
- `tool_args`
- `result_count`
- `latency_ms`
- `model_name`
- `input_tokens`
- `output_tokens`
- `request_id`
- `success`
- `error_message`（如果有）

## 17.2 需要观测的核心指标

- 总 run 完成率
- 各阶段失败率
- 每阶段平均 tool calls 数量
- 每次 run 的总 token 使用量
- 外部源调用命中率 / cache hit rate
- hypothesis 生成成功率
- 平均 selected papers 数量

## 17.3 日志建议

日志分三层：

- `app log`: API、路由、启动、异常
- `agent log`: 每阶段进入/退出、summary、schema validation
- `tool trace log`: 每次工具调用的结构化记录

---

## 18. 错误处理与降级策略

## 18.1 Retrieval 失败

### 可能原因

- OpenAlex 不可用
- Semantic Scholar 不可用
- query 结果过少
- schema 输出失败

### 降级策略

- 单源可用时用单源继续
- 结果过少时自动放宽 query / year range 一次
- 最低可用阈值 12 篇，否则返回 low evidence mode

## 18.2 Review 失败

### 降级策略

- 按批次重试 evidence extraction
- 某批失败不影响其他批
- 最终允许仅部分 papers 产生 evidence cards

## 18.3 Critic 失败

### 降级策略

- 若 critic 完全失败，可直接进入 planner
- planner 在没有 conflict map 时，必须显式增加 limitation / uncertainty 字段

## 18.4 Planner 失败

### 降级策略

- 返回 selected papers + evidence + conflict partial result
- 允许后续只重跑 planner

## 18.5 Structured Output 失败

### 策略

- 先做一次自动重试
- 二次仍失败则通过宿主进行 repair parse
- 若 repair parse 失败，则标记该阶段 failed

---

## 19. 安全边界与可信性规则

## 19.1 Grounding 规则

模型只能使用：

- 用户输入 topic
- 已加载 papers 的 metadata / abstract
- 由这些 metadata/abstract 派生出的 evidence cards
- conflict clusters

禁止：

- 自由引用未检索到的论文
- 编造实验结果
- 编造数值效果
- 声称“已被证明”而无支撑 evidence

## 19.2 假设质量规则

每个 hypothesis 必须：

- 可验证
- 可被反驳
- 有证据支持
- 有证据反例或限制
- 有最小实验路径

## 19.3 Tool 安全规则

V1 不提供：

- shell 工具
- browser 工具
- arbitrary HTTP fetch
- 文件系统写任意路径
- 任意 Python 执行工具

工具只能访问：

- OpenAlex
- Semantic Scholar
- 当前 run 的 workspace

---

## 20. 目录结构与工程组织

```text
repo/
  pyproject.toml
  .env.example
  README.md
  SPEC.md
  app/
    main.py
    config.py
    api/
      routes_runs.py
      schemas.py
    runtime/
      coordinator.py
      agent_runner.py
      tool_dispatcher.py
      tracing.py
      budget.py
    agents/
      retrieval_agent.py
      review_agent.py
      critic_agent.py
      planner_agent.py
      prompts.py
    tools/
      scholarly_tools.py
      workspace_tools.py
      render_tools.py
      schemas.py
    connectors/
      openalex.py
      semantic_scholar.py
      normalizers.py
      dedupe.py
      ranking.py
    services/
      report_renderer.py
      caching.py
      paper_store.py
    db/
      models.py
      session.py
      repository.py
      migrations/
    tests/
      test_openalex_connector.py
      test_s2_connector.py
      test_normalizers.py
      test_dedupe.py
      test_retrieval_agent.py
      test_review_agent.py
      test_critic_agent.py
      test_planner_agent.py
      test_end_to_end.py
  scripts/
    run_topic.py
    seed_demo_runs.py
```

---

## 21. 配置项与环境变量

## 21.1 `.env.example`

```env
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL_RETRIEVAL=gpt-5.4
OPENAI_MODEL_REVIEW=gpt-5-mini
OPENAI_MODEL_CRITIC=gpt-5.4
OPENAI_MODEL_PLANNER=gpt-5.4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

OPENALEX_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=

DATABASE_URL=sqlite:///./app.db
CACHE_BACKEND=memory

MAX_SELECTED_PAPERS=36
MAX_TOOL_STEPS_RETRIEVAL=12
MAX_TOOL_STEPS_REVIEW=6
MAX_TOOL_STEPS_CRITIC=4
MAX_TOOL_STEPS_PLANNER=4
MAX_OPENALEX_CALLS_PER_RUN=20
MAX_S2_CALLS_PER_RUN=20
REQUEST_TIMEOUT_SECONDS=30
ENABLE_FULLTEXT=false
```

## 21.2 配置设计要求

- 所有模型名配置化
- 外部源 key 配置化
- tool budget 配置化
- cache backend 配置化
- fulltext flag 默认 false

---

## 22. 测试策略

## 22.1 测试层次

### 单元测试

覆盖：

- OpenAlex connector
- S2 connector
- normalizer
- dedupe
- ranking
- report renderer

### 集成测试

覆盖：

- Retrieval Agent 的 tool loop
- Review Agent 的 evidence 抽取与保存
- Critic Agent 的 cluster 输出
- Planner Agent 的 hypothesis 输出

### 端到端测试

输入固定 topic，检查：

- run 完成
- selected papers >= 12
- hypotheses == 3
- markdown report 非空
- trace 非空

## 22.2 Golden Topics

建议使用以下 topic 作为回归集：

- `solid-state battery electrolyte`
- `protein binder design`
- `CRISPR delivery lipid nanoparticles`
- `CO2 reduction catalyst selectivity`
- `diffusion model preference optimization`

## 22.3 关键断言

- 不允许 hypothesis 数量不是 3
- 不允许 evidence ids 空数组
- 不允许 Planner 产出没有 experiment 的 hypothesis
- 不允许 report renderer 依赖模型自由文本格式

---

## 23. MVP 验收标准

满足以下条件才算 V1 可交付：

1. 能从 topic 跑通完整流程
2. Retrieval Agent 真实发生多次工具调用
3. 能同时接 OpenAlex 和 Semantic Scholar
4. selected papers 被成功去重并落库
5. Review Agent 输出 schema-valid evidence cards
6. Critic Agent 输出 schema-valid conflict clusters
7. Planner Agent 输出 **恰好 3 个** 假设
8. 每个假设都具备 supporting evidence
9. 每个假设都具备至少一个 limitation / counterevidence
10. 每个假设都具备最小实验路线
11. report markdown 可直接阅读
12. `/trace` 接口可查看 tool call 记录
13. 任一外部源故障时系统可退化而非整体崩溃

---

## 24. 实现优先级与里程碑

## Milestone 1：项目骨架

- 初始化 FastAPI
- 初始化数据库
- 初始化配置和日志
- 打通健康检查

## Milestone 2：连接器

- 实现 OpenAlex connector
- 实现 Semantic Scholar connector
- 实现统一 normalizer
- 实现 dedupe / ranking

## Milestone 3：Tool 宿主

- 实现工具 schema
- 实现 scholarly tools
- 实现 workspace tools
- 实现 trace logging

## Milestone 4：四个 Agents

- Retrieval Agent
- Review Agent
- Critic Agent
- Planner Agent

## Milestone 5：Coordinator + API

- `POST /v1/runs`
- `GET /v1/runs/{id}`
- `GET /v1/runs/{id}/report.md`
- `GET /v1/runs/{id}/trace`

## Milestone 6：测试与回归

- 单元测试
- e2e 测试
- 5 个 golden topics 回归

---

## 25. 交给 Claude Code 的启动说明

下面这段可以原样交给 Claude Code：

```text
请按本 SPEC 初始化一个 Python 3.12 项目，使用 FastAPI、OpenAI Responses API / Agents SDK、Pydantic v2、SQLAlchemy、SQLite。

目标：
实现一个“科研假设生成器”后端服务。
输入 topic，输出：
1) selected papers
2) evidence cards
3) conflict clusters
4) exactly 3 hypotheses
5) final markdown report
6) full tool trace

重要要求：
- v1 必须采用 model-driven tool calling
- 顶层阶段顺序固定为 retrieval -> review -> critic -> planner
- 每个阶段内部由模型自己调用工具
- 不使用 LangGraph 作为 v1 主编排器
- 不使用 AutoGen
- 不要引入 Redis / Celery / Kafka / 向量数据库 / 前端
- 不要默认抓取或解析 PDF 全文
- 所有 tools 用 typed schema
- 工具输出必须是紧凑 JSON
- 每个 agent 只能看到各自工具白名单
- 必须记录完整 tool trace
- 最终 hypotheses 必须严格为 3 个

请优先完成：
1. pyproject.toml
2. app/config.py
3. app/main.py
4. db/models.py
5. connectors/openalex.py
6. connectors/semantic_scholar.py
7. tools/schemas.py
8. tools/scholarly_tools.py
9. tools/workspace_tools.py
10. agents/prompts.py
11. agents/retrieval_agent.py
12. runtime/coordinator.py
13. api/routes_runs.py
14. 最小可运行的 POST /v1/runs
15. pytest 基础测试

完成骨架后，再逐步补全 review / critic / planner。
```

---

## 26. 附录 A：关键 JSON Schema

## 26.1 Run Result

```json
{
  "run_id": "string",
  "status": "queued | retrieving | reviewing | criticizing | planning | done | failed",
  "selected_papers": [],
  "evidence_cards": [],
  "conflict_clusters": [],
  "hypotheses": [],
  "report_markdown": "string | null",
  "trace_url": "string | null"
}
```

## 26.2 PlannerSummary

```json
{
  "hypotheses_created": 3,
  "report_rendered": true,
  "top_axes": ["string"],
  "planner_notes": ["string"]
}
```

---

## 27. 附录 B：示例输出

## 27.1 假设示例（格式示意）

```json
{
  "rank": 1,
  "title": "Interfacial polymer-rich composite electrolytes improve dendrite suppression under moderate stack pressure",
  "hypothesis_statement": "For sulfide-based solid-state batteries, adding a thin polymer-rich interfacial sublayer will reduce interfacial impedance growth and suppress dendrite formation under moderate stack pressure compared with bare sulfide electrolyte interfaces.",
  "why_plausible": "Multiple evidence cards suggest that interfacial instability and pressure sensitivity are major drivers of failure, while composite or coated interfaces show improved stability under comparable conditions.",
  "why_not_obvious": "The benefit may depend on pressure regime and ionic transport penalty, so this is not a universal improvement claim.",
  "supporting_evidence_ids": ["e1", "e4", "e8"],
  "counterevidence_ids": ["e12"],
  "prediction": "Cells with the interfacial sublayer will show lower impedance growth and delayed shorting over 100 cycles at moderate stack pressure.",
  "minimal_experiment": {
    "system": "Li metal | sulfide SSE | cathode half-cell",
    "design": "Compare bare interface vs polymer-rich interlayer across two pressure settings",
    "control": "Bare interface at same pressure and current density",
    "readouts": ["EIS", "cycling stability", "post-mortem interface morphology"],
    "success_criteria": "Lower impedance growth and improved cycle retention without major conductivity penalty",
    "failure_interpretation": "If benefits disappear under matched pressure or transport drops too much, the hypothesis is likely condition-specific or false"
  },
  "risks": ["polymer transport penalty", "pressure confounding"],
  "novelty_score": 0.74,
  "feasibility_score": 0.81,
  "overall_score": 0.78
}
```

---

## 28. 附录 C：官方参考资料

以下资料用于支持本 SPEC 的技术选型与实现边界，建议开发时优先查阅官方文档：

### OpenAI

1. OpenAI Responses API：工具调用、agentic loop
2. OpenAI Agents SDK：specialized agents、handoff、streaming、trace
3. OpenAI Tools / MCP 文档：custom functions、remote MCP、connectors
4. GPT-5.4 / GPT-5-mini 模型文档
5. Streaming Responses 文档

### OpenAlex

1. OpenAlex Overview / API Overview
2. OpenAlex API Introduction
3. OpenAlex Authentication & Pricing

### Semantic Scholar

1. Semantic Scholar Academic Graph API
2. Semantic Scholar Recommendations API
3. Semantic Scholar Graph API Swagger

### 智谱 GLM

1. GLM-5 文档
2. GLM Coding Plan 概览

---

# 结论

本 SPEC 对 V1 的定义非常明确：

- **不是** 传统摘要系统
- **不是** 完全自由 agent swarm
- **而是** 一个“固定阶段顺序 + 阶段内模型端工具调用”的科研假设生成系统

最重要的工程决策：

1. **V1 主编排采用 OpenAI Responses API / Agents SDK**
2. **检索源限定为 OpenAlex + Semantic Scholar**
3. **默认只基于 title/abstract/metadata，不做全文**
4. **输出必须严格结构化，最终固定为 3 个 hypotheses**
5. **必须保留完整 tool trace 以便调试与验收**

如果未来进入 V2，可扩展方向包括：

- LangGraph 状态图编排
- PDF 全文抽取
- 专门的 novelty search 模块
- 人工反馈 rerank
- MCP server 化工具层
- 多轮主题 refine


<!-- Generated: 2026-03-22 | Files scanned: 184 | Token estimate: ~600 -->

# Dependencies Codemap

## External Services

| Service | Purpose | Connector |
|---------|---------|-----------|
| OpenAI Responses API | Agent LLM (tool calling + structured output) | `agents/providers.py` |
| OpenAlex API | Academic paper search | `connectors/openalex.py` |
| Semantic Scholar API | Paper search + recommendations | `connectors/semantic_scholar.py` |
| AlphaXiv MCP | Embedding search, full-text, agentic retrieval | `connectors/alphaxiv.py` |

## Python Dependencies (runtime)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.116, <1 | HTTP framework |
| uvicorn | >=0.35, <1 | ASGI server |
| openai | >=1.108, <2 | LLM client (Responses API) |
| pydantic | >=2.11, <3 | Data validation |
| pydantic-settings | >=2.10, <3 | Environment config |
| sqlalchemy | >=2.0.40, <3 | ORM + SQLite |
| httpx | >=0.28, <1 | HTTP client for connectors |

Dev: `pytest >=8.3, <9`

## JavaScript Dependencies (runtime)

| Package | Version | Purpose |
|---------|---------|---------|
| next | 16.1.6 | Framework |
| react / react-dom | 19.2.3 | UI |
| @tanstack/react-query | ^5.90 | Server state |
| zustand | ^5.0 | Client state |
| zod | ^4.3 | Schema validation |
| react-hook-form | ^7.71 | Form management |
| @hookform/resolvers | ^5.2 | Zod resolver |
| react-markdown | ^10.1 | Markdown rendering |
| lucide-react | ^0.577 | Icons |
| next-themes | ^0.4 | Theme switching |
| sonner | ^2.0 | Toasts |
| clsx + tailwind-merge | ^2.1 / ^3.5 | Class utilities |
| class-variance-authority | ^0.7 | Variant styling |
| @radix-ui/* | various | UI primitives (13 packages) |

Dev: tailwindcss ^4, typescript ^5, eslint ^9, eslint-config-next 16.1.6

## Caching Strategy

| Cache Layer | Storage | TTL | Purpose |
|-------------|---------|-----|---------|
| Raw response cache | SQLite `cache_entries` | 7 days | OpenAlex/S2/AlphaXiv raw responses |
| Normalized paper cache | SQLite `cache_entries` | 30 days | Deduplicated paper payloads |
| Evidence card cache | SQLite `cache_entries` | 30 days | Reuse evidence across runs |
| Validation cache | In-memory (`ValidationCache`) | per-run | Intermediate validation results |

## Budget Controls

| Resource | Default Limit |
|----------|--------------|
| OpenAlex calls/run | 20 |
| Semantic Scholar calls/run | 20 |
| AlphaXiv calls/run | 20 |
| Tool steps: retrieval | 12 |
| Tool steps: review | 6 |
| Tool steps: critic | 4 |
| Tool steps: planner | 4 |
| HTTP timeout | 30s |

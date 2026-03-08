from __future__ import annotations

from typing import Any


def normalize_semantic_scholar_query(query: str) -> str:
    return query.replace("-", " ").strip()


def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def reconstruct_openalex_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    if not inverted_index:
        return None
    positions: dict[int, str] = {}
    for token, indices in inverted_index.items():
        for index in indices:
            positions[index] = token
    if not positions:
        return None
    return " ".join(token for _, token in sorted(positions.items()))


def compact_json_payload(payload: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: payload.get(key) for key in keys if key in payload}


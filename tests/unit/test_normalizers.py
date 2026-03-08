from hypoforge.infrastructure.connectors.normalizers import (
    normalize_semantic_scholar_query,
    normalize_title,
)


def test_semantic_scholar_query_replaces_hyphens() -> None:
    assert normalize_semantic_scholar_query("solid-state battery") == "solid state battery"


def test_normalize_title_trims_and_lowercases() -> None:
    assert normalize_title("  Solid State Battery  ") == "solid state battery"


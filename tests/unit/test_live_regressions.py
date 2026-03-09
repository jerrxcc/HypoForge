from hypoforge.testing.live_regressions import GOLDEN_TOPICS


def test_golden_topics_match_spec_regression_set() -> None:
    assert GOLDEN_TOPICS == (
        "solid-state battery electrolyte",
        "protein binder design",
        "CRISPR delivery lipid nanoparticles",
        "CO2 reduction catalyst selectivity",
        "diffusion model preference optimization",
    )

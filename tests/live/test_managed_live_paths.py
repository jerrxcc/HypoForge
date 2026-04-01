from hypoforge.testing.live_regressions import (
    COMBINED_LIVE,
    REFLECTION_RETRY_LIVE,
    VALIDATION_ONLY_LIVE,
    assert_live_scenario_meets_spec,
    run_live_scenario_round_trip,
)


def test_reflection_retry_live(tmp_path) -> None:
    artifacts = run_live_scenario_round_trip(tmp_path, REFLECTION_RETRY_LIVE)
    assert_live_scenario_meets_spec(
        scenario=REFLECTION_RETRY_LIVE,
        artifacts=artifacts,
    )


def test_validation_only_live(tmp_path) -> None:
    artifacts = run_live_scenario_round_trip(tmp_path, VALIDATION_ONLY_LIVE)
    assert_live_scenario_meets_spec(
        scenario=VALIDATION_ONLY_LIVE,
        artifacts=artifacts,
    )


def test_combined_live(tmp_path) -> None:
    artifacts = run_live_scenario_round_trip(tmp_path, COMBINED_LIVE)
    assert_live_scenario_meets_spec(
        scenario=COMBINED_LIVE,
        artifacts=artifacts,
    )

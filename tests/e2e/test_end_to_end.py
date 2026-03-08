from hypoforge.application.services import build_fake_services


def test_end_to_end_run_returns_three_hypotheses(tmp_path) -> None:
    services = build_fake_services(database_url=f"sqlite:///{tmp_path / 'app.db'}")

    result = services.coordinator.run_topic("CRISPR delivery lipid nanoparticles")

    assert result.status == "done"
    assert len(result.hypotheses) == 3
    assert result.report_markdown
    assert result.trace_url

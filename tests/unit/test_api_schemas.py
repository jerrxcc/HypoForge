from hypoforge.api.schemas import RunRequestBody


def test_run_request_body_defaults_constraints() -> None:
    payload = RunRequestBody(topic="protein binder design")

    assert payload.topic == "protein binder design"
    assert payload.constraints.max_selected_papers == 36

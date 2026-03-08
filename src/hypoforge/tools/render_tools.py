from __future__ import annotations

from hypoforge.infrastructure.db.repository import RunRepository


class RenderTools:
    def __init__(self, repository: RunRepository, renderer) -> None:
        self._repository = repository
        self._renderer = renderer

    def render_markdown_report(self, run_id: str, payload: dict | None = None) -> dict:
        del payload
        result = self._repository.build_final_result(run_id)
        markdown = self._renderer.render(result)
        self._repository.save_report_markdown(run_id, markdown)
        return {"report_markdown": markdown}

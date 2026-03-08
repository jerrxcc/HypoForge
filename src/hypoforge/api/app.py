from fastapi import FastAPI

from hypoforge.api.routes.health import router as health_router
from hypoforge.api.routes.runs import router as runs_router
from hypoforge.application.services import ServiceContainer, build_default_services


def create_app(services: ServiceContainer | None = None) -> FastAPI:
    app = FastAPI(title="HypoForge", version="0.1.0")
    app.state.services = services or build_default_services()
    app.include_router(health_router)
    app.include_router(runs_router)
    return app

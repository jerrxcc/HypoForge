from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hypoforge.api.routes.health import router as health_router
from hypoforge.api.routes.runs import router as runs_router
from hypoforge.application.services import ServiceContainer, build_default_services
from hypoforge.config import Settings


def create_app(
    services: ServiceContainer | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="HypoForge", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.services = services or build_default_services(settings=settings)
    app.include_router(health_router)
    app.include_router(runs_router)
    return app

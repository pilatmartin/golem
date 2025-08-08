"""Main module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette_admin.contrib.sqla import Admin, ModelView

from app.api.v1.routes.auth import auth_router
from app.api.v1.routes.organisms import organisms_router
from app.api.v1.routes.test import test_router
from app.db.db import engine
from app.db.models.group import Group
from app.db.models.organism import Organism
from app.db.models.user import User

V1_PREFIX = "/v1"


def _setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,  # warning: https://github.com/fastapi/fastapi/discussions/10968
        allow_origins=["*"],  # TODO: add allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


def _setup_routes(app: FastAPI) -> None:
    app.include_router(router=test_router, prefix=V1_PREFIX)
    app.include_router(router=auth_router, prefix=V1_PREFIX)
    app.include_router(router=organisms_router, prefix=V1_PREFIX)


def _setup_admin(app: FastAPI) -> None:
    admin = Admin(engine, title="GOLEM Admin")

    admin.add_view(ModelView(Group))
    admin.add_view(ModelView(Organism))
    admin.add_view(ModelView(User))

    admin.mount_to(app)


def create_app() -> FastAPI:
    app = FastAPI(
        title="GOLEM API v1",
        root_path="/api",
    )

    _setup_middleware(app)
    _setup_routes(app)
    _setup_admin(app)

    return app


golem_app = create_app()

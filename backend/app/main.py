"""Main module."""
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette_admin.contrib.sqlmodel import Admin, ModelView

from app.admin.admin_base import AdminViewBase, AdminIndexView
from app.api.v1.middleware.user_loader import UserLoaderMiddleware
from app.api.v1.routes.auth import auth_router
from app.api.v1.routes.organisms import organisms_router
from app.api.v1.routes.test import test_router
from app.db.db import engine, add_default_admin
from app.db.models.group import Group
from app.db.models.organism import Organism
from app.db.models.user import User

V1_PREFIX = "/api/v1"


def _setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,  # warning: https://github.com/fastapi/fastapi/discussions/10968
        allow_origins=["*"],  # TODO: add allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(UserLoaderMiddleware)


def _setup_routes(app: FastAPI) -> None:
    app.include_router(router=test_router, prefix=V1_PREFIX)
    app.include_router(router=auth_router, prefix=V1_PREFIX)
    app.include_router(router=organisms_router, prefix=V1_PREFIX)


def _setup_admin(app: FastAPI) -> None:
    admin = Admin(
        engine=engine,
        title="GOLEM Admin",
        index_view=AdminIndexView(label="GOLEM Admin", path="/"),
    )

    admin.add_view(AdminViewBase(Group))
    admin.add_view(AdminViewBase(Organism))
    admin.add_view(AdminViewBase(User))

    admin.mount_to(app)

    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(add_default_admin(), loop)


def create_app() -> FastAPI:
    app = FastAPI(
        title="GOLEM API v1",
        docs_url=None,
        redoc_url=None,
    )

    _setup_middleware(app)
    _setup_routes(app)
    _setup_admin(app)

    return app


golem_app = create_app()

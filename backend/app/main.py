"""Main module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes.auth import auth_router
from app.api.v1.routes.test import test_router

V1_PREFIX = "/v1"


def create_app():
    app = FastAPI(
        title="GOLEM API v1",
        root_path="/api",
    )

    app.add_middleware(
        CORSMiddleware,  # warning: https://github.com/fastapi/fastapi/discussions/10968
        allow_origins=["*"],  # TODO: add allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.include_router(router=test_router, prefix=V1_PREFIX)
    app.include_router(router=auth_router, prefix=V1_PREFIX)

    return app


golem_app = create_app()

from fastapi import Request, Response
from starlette.responses import RedirectResponse
from starlette.status import HTTP_404_NOT_FOUND
from starlette.templating import Jinja2Templates
from starlette_admin import CustomView
from starlette_admin.contrib.sqlmodel import ModelView

from app.db.models.user import User
from app.services.auth import is_admin

# TODO: figure out how to synchronously get the user without
#       having to use both the middleware and the dependency (db is accessed twice)

class AdminIndexView(CustomView):
    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        user: User = request.state.user
        if not is_admin(user):
            return RedirectResponse(url="/", status_code=HTTP_404_NOT_FOUND)

        return RedirectResponse(url="organism/list")


class AdminViewBase(ModelView):
    def is_accessible(self, request: Request) -> bool:
        user: User = request.state.user
        return is_admin(user)

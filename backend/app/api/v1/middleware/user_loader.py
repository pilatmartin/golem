from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.services.auth import get_user_from_token

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class UserLoaderMiddleware(BaseHTTPMiddleware):
    """Middleware used for getting user from token stored in cookie."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.user = None
        token = request.cookies.get("access_token")

        if token:
            user = await get_user_from_token(token)
            request.state.user = user

        response = await call_next(request)
        return response

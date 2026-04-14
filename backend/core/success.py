import typing
from fastapi import Request, Response
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.logger import logger

class Success(APIRoute):
    def get_route_handler(self) -> typing.Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except (RequestValidationError, StarletteHTTPException) as exc:
                raise exc
            except Exception as e:
                logger.exception(f"Exception in route {self.path}:")
                return JSONResponse(
                    content={"code": -1, "msg": str(e)}
                )

        return custom_route_handler

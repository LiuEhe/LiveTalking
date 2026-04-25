"""
统一接口异常包装器。

这个类通过继承 `APIRoute`，把每个接口真正执行前后包一层 try/except。
它的价值是：
- 业务代码可以更专注于主流程
- 未捕获异常能统一返回 `{"code": -1, "msg": ...}`
- 方便前端按统一格式处理错误
"""

import typing
from fastapi import Request, Response
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.logger import logger


class Success(APIRoute):
    """自定义路由类：统一兜底异常，并输出标准 JSON 结构。"""

    def get_route_handler(self) -> typing.Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                # 正常情况下，交给真正的接口函数执行。
                return await original_route_handler(request)
            except (RequestValidationError, StarletteHTTPException) as exc:
                # 参数校验错误和标准 HTTP 异常交给 FastAPI 自己处理，
                # 这样可以保留更规范的状态码和报错格式。
                raise exc
            except Exception as e:
                logger.exception(f"Exception in route {self.path}:")
                return JSONResponse(content={"code": -1, "msg": str(e)})

        return custom_route_handler

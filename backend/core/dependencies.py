"""
FastAPI 依赖注入函数。

这类函数通常会被接口通过 `Depends(...)` 引入，用来做鉴权、限流、权限校验等。
目前这里只有一个简单的 token 解析示例。
"""

from fastapi import Header, HTTPException
from core.security import verify_token


async def get_token_header(x_token: str = Header(default=None)):
    """
    从请求头读取 `X-Token` 并尝试解析。

    当前策略比较宽松：
    - 不传 token：直接返回 `None`
    - 传了但不合法：返回 401
    """
    if x_token is None:
        return None
        # 如果你后面要把接口改成“必须登录才能访问”，
        # 可以把这里放开的逻辑改成直接抛异常。
        # raise HTTPException(status_code=400, detail="X-Token header invalid")
    payload = verify_token(x_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

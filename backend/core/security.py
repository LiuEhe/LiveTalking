"""
简单的 JWT 工具函数。

这部分目前只是演示级实现，适合本地开发和理解流程。
如果后面要上线，请至少处理以下问题：
- 不要把密钥硬编码在仓库里
- 区分 access token / refresh token
- 结合用户体系做权限校验
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = "your-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """根据输入载荷创建一个 JWT 字符串。"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """校验 JWT；成功返回载荷，失败返回 `None`。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

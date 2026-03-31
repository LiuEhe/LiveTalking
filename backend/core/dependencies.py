from fastapi import Header, HTTPException
from core.security import verify_token

async def get_token_header(x_token: str = Header(default=None)):
    if x_token is None:
        return None
        # Raise exception if strict auth is needed
        # raise HTTPException(status_code=400, detail="X-Token header invalid")
    payload = verify_token(x_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

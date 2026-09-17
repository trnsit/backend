from uuid import UUID

from pydantic import BaseModel

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer

from .config import settings
from ..security.jwt import decode_access_token

# Look for 'Authorization: Bearer <token>' header in incoming requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

class CurrentUser(BaseModel):
    id: UUID
    email: str

async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    payload = decode_access_token(token)

    if not payload:
        raise credentials_exception

    email: str | None = payload.get('sub')
    user_id_str: str | None = payload.get('user_id')

    if not email or not user_id_str:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)

    except ValueError:
        raise credentials_exception

    return CurrentUser(id=user_id, email=email)

async def verify_internal_token(x_internal_token: str = Header(...)) -> None:
    """ When you declare a parameter in a FastAPI function:
        - If you write token: str, FastAPI looks for ?token=... in the URL query string.
        - But when you write x_internal_token: str = Header(...), you are telling FastAPI:
            "Do not look in the URL. Look specifically in the HTTP Request Headers for X-Internal-Token."

    FastAPI is smart enough to automatically convert Python's snake_case x_internal_token to the standard HTTP header format X-Internal-Token. """

    if x_internal_token != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied: Invalid internal service token'
        )

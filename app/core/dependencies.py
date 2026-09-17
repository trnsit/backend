from uuid import UUID

from pydantic import BaseModel

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.security.jwt import decode_access_token

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

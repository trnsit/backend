from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

from .db.session import get_session
from app.security.jwt import decode_access_token
from .models import User
from .store import UserStore
from .service import UserService

# oauth2_scheme looking for token in 'Authorization: Bearer <token>' header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login') # Use standard url or register

""" OAuth2PasswordBearer automatically:
    1. Finds the Authorization header.
    2. Strips away the word "Bearer " and extracts just the raw token string.
    3. Adds the little Green Padlock / "Authorize" button in FastAPI's Swagger UI documentation. """

def get_user_store(session: AsyncSession = Depends(get_session)) -> UserStore:
    return UserStore(session)

def get_user_service(user_store: UserStore = Depends(get_user_store)) -> UserService:
    return UserService(user_store)

async def get_current_user(token: str = Depends(oauth2_scheme), service: UserService = Depends(get_user_service)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    email: str = payload.get('sub')
    if email is None:
        raise credentials_exception
        
    user = await service.store.authenticate(email)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail='User account is inactive or disabled'
        )
        
    return user

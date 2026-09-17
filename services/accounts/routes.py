from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.security.jwt import create_access_token
from .dependencies import get_user_service, get_current_user
from .schemas import UserCreate, UserResponse, Token, Login
from .service import UserService

router = APIRouter(tags=['accounts'])

# AUTH ENDPOINTS:
@router.post('/register', response_model=UserResponse)
# Pass the get_user_service function as the dependency
async def create_user(user: UserCreate, service: UserService = Depends(get_user_service)):  # The Depends function represents the function as the dependency for FastAPI to manage its lifecycle.
    return await service.create(user)

@router.post('/login', response_model=Token)
async def login(login_data: Login, service: UserService = Depends(get_user_service)):
    user = await service.login(login_data)
    access_token = create_access_token(data={'sub': user.email, 'user_id': str(user.id)})

    return {'access_token': access_token, 'token_type': 'bearer'}

@router.get('/users/me', response_model=UserResponse)
async def profile(current_user = Depends(get_current_user)):
    return current_user

# INTERNAL COMMUNICATION ENDPOINT:
@router.get('/internal/users/{user_id}/tokens/{provider}')
async def get_user_auth_token(user_id: UUID, provider: str, service: UserService = Depends(get_user_service)):
    token = await service.get_oauth_token(user_id, provider)

    if not token:
        raise HTTPException(
            status_code=404,
            detail=f'Token for provider {provider} not found'
        )

    return {'access_token': token}

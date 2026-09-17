from uuid import UUID

from fastapi import HTTPException # An exception that FastAPI handles.

from .models import User
from .store import UserStore
from .schemas import UserCreate, UserResponse, Login
from app.security.password import hash_password, verify_password

class UserService:
    def __init__(self, user_store: UserStore):
        self.store = user_store

    # Make the method capable of receiving email, and getting the user object by the use of UserService
    async def authenticate(self, email) -> UserResponse:
        user = await self.store.authenticate(email)

        if not user:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )

        return user

    async def login(self, login_data: Login) -> User:
        user = await self.store.authenticate(login_data.email)

        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail='Incorrect email or password'
            )

        return user

    async def create(self, user: UserCreate) -> User:
        if await self.store.authenticate(user.email):
            raise HTTPException(
                status_code=409,
                detail='User already exists'
            )

        password_hash = hash_password(user.password)

        return await self.store.create(
            email=user.email,
            password_hash=password_hash
        )

    async def get_oauth_token(self, user_id: UUID, provider: str) -> str | None:
        token = await self.store.get_oauth_token(user_id, provider)

        return token.access_token if token else None

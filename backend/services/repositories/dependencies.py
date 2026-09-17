from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from .db.session import get_session
from .store import RepositoryStore
from .service import RepositoryService
from .clients.accounts import AccountsClient

def get_repository_store(session: AsyncSession = Depends(get_session)) -> RepositoryStore:
    return RepositoryStore(session)

def get_repository_service(store: RepositoryStore = Depends(get_repository_store)) -> RepositoryService:
    return RepositoryService(store)

def get_accounts_client() -> AccountsClient:
    return AccountsClient()

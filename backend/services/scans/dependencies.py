from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from .db.session import get_session
from .store import ScanStore
from .service import ScanService
from .clients.accounts import AccountsClient
from .clients.repositories import RepositoriesClient

def get_scan_store(session: AsyncSession = Depends(get_session)) -> ScanStore:
    return ScanStore(session)

def get_scan_service(scan_store: ScanStore = Depends(get_scan_store)) -> ScanService:
    return ScanService(scan_store)

def get_accounts_client() -> AccountsClient:
    return AccountsClient()

def get_repositories_client() -> RepositoriesClient:
    return RepositoriesClient()

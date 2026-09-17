from uuid import UUID

from fastapi import APIRouter, Depends, status, BackgroundTasks, HTTPException

from app.core.dependencies import CurrentUser, get_current_user, verify_internal_token
from .dependencies import get_scan_service, get_accounts_client, get_repositories_client
from .clients.accounts import AccountsClient
from .clients.repositories import RepositoriesClient
from .service import ScanService
from .schemas import ScanResponse

router = APIRouter(prefix='/scans', tags=['scans'])

# 1. Trigger when user clicks the "Start Scan" button -> ScanService.trigger_scan
@router.post('/repository/{repository_id}', response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan(
    repository_id: UUID,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    service: ScanService = Depends(get_scan_service),
    accounts_client: AccountsClient = Depends(get_accounts_client),
    repos_client: RepositoriesClient = Depends(get_repositories_client)
):
    """ BackgroundTasks is a special built-in "VIP" type in FastAPI (also are Request, Response, and WebSocket)
    that it recognizes instantly without needing Depends. """

    # 1. Fetch repo info via internal client (verifies user ownership)
    repo = await repos_client.get_repository(user.id, repository_id)

    if not repo:
        raise HTTPException(
            status_code=404,
            detail='Repository not found'
        )

    # 2. Fetch GitHub token via internal client
    token = await accounts_client.get_github_token(user.id)

    if not token and repo.is_private:
        raise HTTPException(
            status_code=400,
            detail='GitHub account not connected. Please connect your GitHub account to scan private repositories.'
        )

    # 3. Trigger the scan
    return await service.trigger_scan(
        user_id=user.id,
        repository_id=repository_id,
        repo_full_name=repo.full_name,
        token=token,
        background_tasks=background_tasks
    )

@router.get('/{scan_id}', response_model=ScanResponse)
async def get_scan_details(
    scan_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: ScanService = Depends(get_scan_service)
):
    return await service.get_scan(user.id, scan_id)

@router.get('/repository/{repository_id}', response_model=list[ScanResponse])
async def list_scans_by_repository(
    repository_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: ScanService = Depends(get_scan_service)
):
    return await service.list_scans(user.id, repository_id)

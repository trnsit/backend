from uuid import UUID

from fastapi import Depends, APIRouter, status, HTTPException

from app.core.dependencies import CurrentUser, get_current_user
from .dependencies import get_repository_service, get_accounts_client
from .clients.accounts import AccountsClient
from .schemas import RepositoryCreate, RepositoryUpdate, RepositoryResponse
from .service import RepositoryService

router = APIRouter(prefix='/repositories', tags=['repositories'])

# API CRUD ENDPOINTS:
@router.get('/{repository_id}', response_model=RepositoryResponse)
async def get_repository_by_id(repository_id: UUID, user: CurrentUser = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.get_by_id(user.id, repository_id)

@router.get('', response_model=list[RepositoryResponse])
async def list_repository_by_user(user: CurrentUser = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.list_by_user(user.id)

@router.post('', response_model=RepositoryResponse)
async def create_repository(data: RepositoryCreate, user: CurrentUser = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.create(user.id, data)

@router.patch('/{repository_id}', response_model=RepositoryResponse)
async def update_repository(data: RepositoryUpdate, repository_id: UUID, user: CurrentUser = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.update(user.id, repository_id, data)

@router.delete('/{repository_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(repository_id: UUID, user: CurrentUser = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service)):
    return await service.delete(user.id, repository_id)

# REMOTE REPOSITORY ENDPOINT:
@router.get('/github/remote', response_model=list[RepositoryCreate])
async def list_remote_github_repositories(user: CurrentUser = Depends(get_current_user), service: RepositoryService = Depends(get_repository_service), accounts_client: AccountsClient = Depends(get_accounts_client)):
    token = await accounts_client.get_github_token(user.id)

    if not token:
        raise HTTPException(
            status_code=400,
            detail='GitHub account not connected. Please connect your GitHub account first.'
        )

    return await service.list_github_repositories(token)

# INTERNAL COMMUNICATION ENDPOINT:
@router.get('/internal/users/{user_id}/repositories/{repository_id}', response_model=RepositoryResponse)
async def get_internal_repository(repository_id: UUID, user_id: UUID, service: RepositoryService = Depends(get_repository_service)):
    return await service.get_by_id(user_id, repository_id)

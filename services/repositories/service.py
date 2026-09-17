import httpx

from uuid import UUID

from fastapi import HTTPException

from .models import Repository
from .schemas import RepositoryCreate, RepositoryUpdate
from .store import RepositoryStore

class RepositoryService:
    def __init__(self, store: RepositoryStore):
        self.store = store

    async def get_by_id(self, user_id: UUID, repository_id: UUID) -> Repository:
        result = await self.store.get_by_id(user_id, repository_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail='Repository not found'
            )

        return result

    async def list_by_user(self, user_id: UUID) -> list[Repository]:
        return await self.store.list_by_user(user_id)

    async def create(self, user_id: UUID, data: RepositoryCreate) -> Repository:
        return await self.store.create(user_id, data)

    async def update(self, user_id: UUID, repository_id: UUID, data: RepositoryUpdate) -> Repository:
        result = await self.store.update(user_id, repository_id, data)

        if not result:
            raise HTTPException(
                status_code=404,
                detail='Repository not found'
            )

        return result

    async def delete(self, user_id, repository_id) -> bool:
        result = await self.store.delete(user_id, repository_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail='Repository not found'
            )

        return result

    async def list_github_repositories(self, token: str):
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Transit-App'
            }

            response = await client.get(
                'https://api.github.com/user/repos?per_page=100&sort=updated',
                headers=headers
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch repositories from GitHub: {response.text}"
                )

            repositories = response.json()

            return [
                {
                    "provider": "github",
                    "external_repo_id": str(repo["id"]),
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "url": repo["html_url"],
                    "default_branch": repo["default_branch"],
                    "is_private": repo["private"]
                }
                for repo in repositories
            ]

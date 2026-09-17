import os
import httpx

from uuid import UUID

from fastapi import HTTPException

from pydantic import BaseModel

class RepositoryInfo(BaseModel):
    id: UUID
    full_name: str
    is_private: bool = False

class RepositoriesClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv('REPOSITORIES_SERVICE_URL', 'http://127.0.0.1:8002')

    async def get_repository(self, user_id: UUID, repository_id: UUID) -> RepositoryInfo | None:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f'{self.base_url}/repositories/internal/users/{user_id}/repositories/{repository_id}',
                    timeout=10.0
                )

                if response.status_code == 404:
                    return None

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail='Failed to retrieve repository from Repositories service'
                    )

                data = response.json()

                return RepositoryInfo(**data)

            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f'Repositories service unavailable: {str(exc)}'
                )

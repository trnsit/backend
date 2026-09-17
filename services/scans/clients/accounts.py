import os
import httpx

from uuid import UUID

from fastapi import HTTPException

class AccountsClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv('ACCOUNTS_SERVICE_URL', 'http://127.0.0.1:8001')

    async def get_github_token(self, user_id: UUID) -> str | None:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f'{self.base_url}/internal/users/{user_id}/tokens/github',
                    timeout=10.0
                )

                if response.status_code == 404:
                    return None

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail='Failed to retrieve token from Accounts service'
                    )

                data = response.json()
                return data.get('access_token')

            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f'Accounts service unavailable: {str(exc)}'
                )

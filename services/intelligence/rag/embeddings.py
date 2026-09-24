import httpx

from ..config import settings

async def get_embedding(text: str) -> list[float]:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/embeddings"

    payload = {
        'model': settings.qdrant_embedding_model,
        'prompt': text
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)

        if response.status_code != 200:
            raise RuntimeError(
                f'Failed to generate embedding from Ollama: {response.status_code} - {response.text}'
            )

        data = response.json()

        return data['embedding']

from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from ..config import settings
from .embeddings import get_embedding

COLLECTION_NAME = 'pqc_knowledge_base'
VECTOR_SIZE = 768

class VectorStore:
    def __init__(self, url: str | None = None):
        self.url = url or settings.qdrant_url
        self.client = AsyncQdrantClient(url=self.url)

    # Creates the Qdrant collection if it doesn't already exist.
    async def init_collection(self):
        collections = await self.client.get_collections()
        existing_names = [col.name for col in collections.collections]

        if COLLECTION_NAME not in existing_names:
            await self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE
                )
            )

            print(f"Created Qdrant collection '{COLLECTION_NAME}' successfully.")

    # Embeds text and saves it into Qdrant as a Point.
    async def add_document(self, title: str, category: str, content: str, source: str = 'NIST'):
        vector = await get_embedding(content)
        point = models.PointStruct(
            id=str(uuid4()),
            vector=vector,
            payload={
                'title': title,
                'category': category,
                'content': content,
                'source': source
            }
        )

        await self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point]
        )

    # Embeds the query, searches Qdrant for the closest semantic matches, and returns the document payloads.
    async def search(self, query: str, limit: int = 3) -> list[dict]:
        query_vector = await get_embedding(query)
        results = await self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit
        )

        return [point.payload for point in results.points if point.payload]

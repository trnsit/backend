from app.core.config import BaseServiceSettings

class IntelligenceSettings(BaseServiceSettings):
    ollama_base_url: str = 'http://localhost:11434'
    ollama_model: str = 'llama3'

    qdrant_url: str = 'http://localhost:6333'
    qdrant_embedding_model: str = 'nomic-embed-text'

settings = IntelligenceSettings()

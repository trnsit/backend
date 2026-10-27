from app.core.config import BaseServiceSettings

class IntelligenceSettings(BaseServiceSettings):
    ollama_base_url: str = 'http://localhost:11434'
    ollama_model: str = 'llama3'
    ollama_embedding_model: str = 'nomic-embed-text'

    qdrant_url: str = 'http://localhost:6333'

settings = IntelligenceSettings()

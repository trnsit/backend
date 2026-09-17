from app.core.config import BaseServiceSettings

class IntelligenceSettings(BaseServiceSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

settings = IntelligenceSettings()

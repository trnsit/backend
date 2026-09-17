from app.core.config import BaseServiceSettings

class RepositoriesSettings(BaseServiceSettings):
    repositories_database_url: str

settings = RepositoriesSettings()

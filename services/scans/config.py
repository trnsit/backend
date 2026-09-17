from app.core.config import BaseServiceSettings

class ScansSettings(BaseServiceSettings):
    scans_database_url: str

settings = ScansSettings()

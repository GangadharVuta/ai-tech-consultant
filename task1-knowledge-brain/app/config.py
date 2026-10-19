import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Tech Consultant - Knowledge Brain"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Base directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CACHE_DIR: Path = DATA_DIR / "cache"
    MANIFEST_FILE: Path = DATA_DIR / "manifest.json"
    INDEX_FILE: Path = DATA_DIR / "knowledge_index.json"
    ESCALATIONS_FILE: Path = DATA_DIR / "escalations.json"
    
    # Crawler settings
    SITEMAP_URL: str = "https://support.brilliantdirectories.com/support/sitemap.xml"
    CRAWL_DELAY_SECONDS: float = 0.25
    MAX_CONCURRENCY: int = 4
    REQUEST_TIMEOUT: int = 15
    USER_AGENT: str = "AITechConsultantBot/1.0 (+https://example.com/bot; polite-eval-crawler)"
    
    # LLM Settings
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    PRIMARY_MODEL: str = "claude-3-5-sonnet-20241022"
    FAST_MODEL: str = "claude-3-5-haiku-20241022"
    CONFIDENCE_THRESHOLD: float = 0.62
    
    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8001

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)

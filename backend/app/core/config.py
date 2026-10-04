from pathlib import Path
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = REPOSITORY_ROOT / ".env"
if not DEFAULT_ENV_FILE.exists() and (REPOSITORY_ROOT / "backend" / ".env").exists():
    DEFAULT_ENV_FILE = REPOSITORY_ROOT / "backend" / ".env"

class Settings(BaseSettings):
    APP_NAME: str = "MedGraph"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SQL_ECHO: bool = False
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://medgraph:medgraph@localhost:5432/medgraph"
    DATABASE_URL_SYNC: str = "postgresql://medgraph:medgraph@localhost:5432/medgraph"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    UPLOAD_DIR: str = "./data/uploads"
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".png", ".jpg", ".jpeg"]
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf", "image/png", "image/jpeg"]
    AI_PROVIDER: str = "local"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OCR_PROVIDER: str = "auto"
    TESSERACT_CMD: Optional[str] = None
    OCR_LANGUAGE: str = "eng"
    OCR_MIN_TEXT_CHARS: int = 24
    OCR_MAX_PAGES: int = 100
    OCR_RENDER_DPI: int = 220
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost"]
    DEMO_MODE: bool = True

    model_config = SettingsConfigDict(env_file=DEFAULT_ENV_FILE, extra="ignore")

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENVIRONMENT.lower() == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if not self.SECRET_KEY or self.SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError("Set a unique SECRET_KEY in production")
            if self.DEMO_MODE:
                raise ValueError("DEMO_MODE must be false in production")
        return self

settings = Settings()

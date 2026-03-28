"""
Automated Answer Sheet Evaluation System - Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Automated Evaluation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Groq LLM
    GROQ_API_KEY: str = ""
    

    
    # Database (MySQL)
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/evaluation_db"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = ["pdf", "png", "jpg", "jpeg", "txt", "ppt", "pptx"]
    
    # OCR
    TESSERACT_CMD: str = "/usr/bin/tesseract"  # Update for your system
    POPPLER_PATH: str = ""  # Windows: C:\poppler\poppler-xx\Library\bin


    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15
    
    # Database
    database_url: str = "sqlite:///./lawlens.db"
    
    # LLM Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    max_tokens: int = 4000
    
    # Rate Limiting
    redis_url: str = "redis://localhost:6379"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # File Upload Security
    max_file_size_mb: int = 10
    allowed_mime_types: List[str] = [
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # CORS
    # include the dev port 3001 and allow any localhost origin for ease of testing
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "https://localhost:3000",
        "http://localhost:3001",
        "https://localhost:3001",
    ]
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/lawlens.log"
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    class Config:
        env_file = ".env"

settings = Settings()

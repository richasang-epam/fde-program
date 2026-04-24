"""
Configuration management for HR Onboarding Agent.
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/onboarding")

    # External APIs
    workday_api_key: Optional[str] = None
    servicenow_api_key: Optional[str] = None
    lms_api_key: Optional[str] = None
    email_client_id: Optional[str] = None
    email_client_secret: Optional[str] = None
    i9_system_api_key: Optional[str] = None
    bg_check_api_key: Optional[str] = None

    # OpenAI/LangChain
    openai_api_key: str = Field(default="")
    langchain_tracing: bool = Field(default=False)

    # Security
    encryption_key: str = Field(default="your-32-byte-encryption-key-here")
    jwt_secret_key: str = Field(default="your-jwt-secret-key-here")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24)

    # Application
    app_name: str = Field(default="HR Onboarding Agent")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    # SLA Settings
    default_task_timeout_hours: int = Field(default=24)
    escalation_timeout_hours: int = Field(default=4)
    max_retry_attempts: int = Field(default=3)

    # Known Jurisdictions for Compliance
    known_jurisdictions: list = Field(default=[
        "US", "CA", "UK", "DE", "FR", "AU", "JP", "SG"
    ])

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
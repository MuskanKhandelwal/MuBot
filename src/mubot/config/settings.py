"""
Settings Management Module

This module defines all configuration settings for MuBot using Pydantic Settings.
It automatically loads values from environment variables and .env files, providing:
- Type safety and validation
- Default values
- Documentation for each setting
- Runtime access via get_settings()

Example usage:
    from config import get_settings
    
    settings = get_settings()
    print(settings.max_daily_emails)
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration for MuBot.
    
    All settings can be overridden via environment variables or .env file.
    See .env.example for a complete list of available options.
    """
    
    # =========================================================================
    # Pydantic Configuration
    # =========================================================================
    model_config = SettingsConfigDict(
        # Load from .env file
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow extra fields for forward compatibility
        extra="ignore",
        # Enable case-sensitive environment variable names
        case_sensitive=False,
    )
    
    # =========================================================================
    # LLM Provider Settings
    # =========================================================================
    llm_provider: Literal["openai", "anthropic", "kimi"] = Field(
        default="openai",
        description="AI provider to use for text generation",
    )
    
    openai_api_key: Optional[str] = Field(
        default=None,
        description="API key for OpenAI",
    )
    
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="API key for Anthropic",
    )
    
    kimi_api_key: Optional[str] = Field(
        default=None,
        description="API key for Kimi",
    )
    
    llm_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Model to use for generation",
    )
    
    llm_thinking_mode: bool = Field(
        default=False,
        description="Enable thinking mode for complex reasoning",
    )
    
    # =========================================================================
    # Gmail API Settings
    # =========================================================================
    gmail_credentials_path: Path = Field(
        default=Path("./credentials/gmail_credentials.json"),
        description="Path to Google OAuth credentials file",
    )
    
    gmail_token_path: Path = Field(
        default=Path("./credentials/gmail_token.json"),
        description="Path to store OAuth tokens",
    )
    
    sender_email: str = Field(
        default="",
        description="Primary email address for sending",
    )
    
    outreach_label_prefix: str = Field(
        default="outreach",
        description="Gmail label prefix for organizing emails",
    )
    
    # =========================================================================
    # Vector Store (RAG) Settings
    # =========================================================================
    chroma_db_path: Path = Field(
        default=Path("./data/vector_store"),
        description="Directory for ChromaDB files",
    )
    
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings",
    )
    
    rag_max_documents: int = Field(
        default=200,
        ge=10,
        le=1000,
        description="Maximum past emails to index for RAG",
    )
    
    # =========================================================================
    # Memory Settings
    # =========================================================================
    memory_base_path: Path = Field(
        default=Path("./data"),
        description="Base directory for all memory files",
    )
    
    max_daily_emails: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum emails to send per day (safety limit)",
    )
    
    max_followups: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum follow-ups per thread",
    )
    
    default_followup_delay_days: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Default delay before sending follow-up",
    )
    
    # =========================================================================
    # Scheduler Settings
    # =========================================================================
    heartbeat_interval_minutes: int = Field(
        default=60,
        ge=5,
        le=1440,
        description="How often to run heartbeat checks",
    )
    
    scheduler_timezone: Optional[str] = Field(
        default=None,
        description="Timezone for scheduling (uses system if not set)",
    )
    
    # =========================================================================
    # Safety Settings
    # =========================================================================
    require_send_approval: bool = Field(
        default=True,
        description="Require explicit approval before sending emails",
    )
    
    rate_limiting_enabled: bool = Field(
        default=True,
        description="Enable rate limiting between emails",
    )
    
    min_email_interval_seconds: int = Field(
        default=300,
        ge=0,
        description="Minimum seconds between emails",
    )
    
    # =========================================================================
    # Notion Integration (Optional)
    # =========================================================================
    notion_api_token: Optional[str] = Field(
        default=None,
        description="Notion API token for job pipeline",
    )
    
    notion_database_id: Optional[str] = Field(
        default=None,
        description="Notion database ID for applications",
    )
    
    # =========================================================================
    # Logging Settings
    # =========================================================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging verbosity level",
    )
    
    json_logging: bool = Field(
        default=False,
        description="Use structured JSON logging",
    )
    
    # =========================================================================
    # Validators
    # =========================================================================
    @validator("sender_email")
    def validate_email(cls, v: str) -> str:
        """Basic email format validation."""
        if v and "@" not in v:
            raise ValueError(f"Invalid email format: {v}")
        return v
    
    @validator("memory_base_path", "chroma_db_path")
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached Settings instance.
    
    Using lru_cache ensures we only load and validate settings once,
    improving performance for repeated access.
    
    Returns:
        Settings: Validated configuration instance
    """
    return Settings()

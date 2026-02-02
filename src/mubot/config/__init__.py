# =============================================================================
# Configuration Package
# =============================================================================
# This package centralizes all configuration management for MuBot.
# It uses Pydantic Settings to load configuration from environment variables
# and .env files, providing type safety and validation.
# =============================================================================

from mubot.config.settings import Settings, get_settings
from mubot.config.prompts import (
    SYSTEM_PROMPT,
    EMAIL_DRAFT_PROMPT,
    EMAIL_PERSONALIZE_PROMPT,
    FOLLOWUP_PROMPT,
    RESPONSE_CLASSIFY_PROMPT,
)

__all__ = [
    "Settings",
    "get_settings",
    "SYSTEM_PROMPT",
    "EMAIL_DRAFT_PROMPT",
    "EMAIL_PERSONALIZE_PROMPT",
    "FOLLOWUP_PROMPT",
    "RESPONSE_CLASSIFY_PROMPT",
]

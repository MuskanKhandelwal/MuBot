# =============================================================================
# Templates Package
# =============================================================================
# Email and prompt templates for MuBot.
# =============================================================================

from mubot.templates.email_templates import (
    get_cold_email_template,
    get_followup_template,
    get_unsubscribe_footer,
)

__all__ = [
    "get_cold_email_template",
    "get_followup_template",
    "get_unsubscribe_footer",
]

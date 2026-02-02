"""
Email Templates

Pre-built email templates for common job search scenarios.
These serve as starting points that the AI personalizes.

Template Philosophy:
- Templates provide structure, not content
- Every template includes personalization placeholders
- All templates include unsubscribe language
- Templates are optimized for mobile reading (short paragraphs)
"""

from enum import Enum


class EmailTemplateType(Enum):
    """Available email template types."""
    COLD_OUTREACH = "cold_outreach"
    REFERRAL_REQUEST = "referral_request"
    FOLLOW_UP = "follow_up"
    THANK_YOU = "thank_you"
    NETWORKING = "networking"


# =============================================================================
# Base Templates
# =============================================================================

COLD_OUTREACH_TEMPLATE = """Hi {recipient_name},

{personalized_hook}

I'm reaching out because I'm interested in the {role_title} role at {company_name}. {why_interested}

{relevant_experience}

{value_proposition}

Would you be open to a brief conversation about the role and how I might contribute to {company_name}?

{signature}

"""

REFERRAL_REQUEST_TEMPLATE = """Hi {recipient_name},

{personalized_hook}

I'm applying for the {role_title} position at {company_name} and would greatly appreciate your referral. {connection_context}

{relevant_experience}

I understand you're busy, so I've attached my resume and a brief summary of my qualifications for your reference. No pressure at all if you're not comfortable—I'd value any advice you might have either way.

Thank you for considering!

{signature}

"""

FOLLOW_UP_TEMPLATE = """Hi {recipient_name},

I hope this message finds you well. I wanted to follow up on my email from {days_ago} days ago regarding the {role_title} position at {company_name}.

{value_add}

I completely understand if you have a full inbox. If there's a better way to reach you or if you'd prefer I check back at a later time, please let me know.

Thanks for your time!

{signature}

"""

THANK_YOU_TEMPLATE = """Hi {recipient_name},

Thank you so much for taking the time to {conversation_type} today. I really enjoyed learning more about {company_name} and the {role_title} position.

{specific_detail}

I'm very excited about the opportunity to {contribution}. Please don't hesitate to reach out if you need any additional information from me.

Thanks again, and I hope to hear from you soon!

{signature}
"""

NETWORKING_TEMPLATE = """Hi {recipient_name},

{personalized_hook}

I'm currently exploring new opportunities in {field} and came across your profile. {why_reaching_out}

I'd love to learn more about your experience at {company_name} and any insights you might have about the industry. Would you be open to a brief coffee chat or virtual meeting?

I completely understand if you're busy—any advice you could share would be greatly appreciated.

Thanks for your time!

{signature}

"""


# =============================================================================
# Template Functions
# =============================================================================

def get_cold_email_template(
    tone: str = "friendly",
    include_referral_ask: bool = False,
) -> str:
    """
    Get a cold email template.
    
    Args:
        tone: "formal", "friendly", or "bold"
        include_referral_ask: Whether to ask for referral
    
    Returns:
        Template string with placeholders
    """
    base = COLD_OUTREACH_TEMPLATE
    
    if tone == "formal":
        # More formal language
        base = base.replace("Hi", "Dear").replace("Hey", "Hello")
    elif tone == "bold":
        # More confident, direct language
        base = base.replace("Would you be open to", "I'd like to schedule")
    
    if include_referral_ask:
        base = base.replace(
            "Would you be open to a brief conversation",
            "If you're not the right person to speak with, would you be able to point me toward someone on the hiring team? Alternatively, I'd love to"
        )
    
    return base


def get_followup_template(
    followup_number: int = 1,
    tone: str = "polite",
) -> str:
    """
    Get a follow-up email template.
    
    Args:
        followup_number: Which follow-up (1, 2, or 3)
        tone: "polite", "brief", or "value_add"
    
    Returns:
        Template string
    """
    if followup_number == 1:
        # First follow-up: gentle reminder
        value_add = "I recently {recent_accomplishment} and thought it might be relevant to your team's work."
    elif followup_number == 2:
        # Second follow-up: brief, assume busy
        value_add = "I know you're likely juggling many priorities. I wanted to make sure my message didn't get buried."
    else:
        # Third follow-up: final attempt, graceful exit
        value_add = "This will be my last follow-up, as I don't want to clutter your inbox. If now isn't the right time, I completely understand."
    
    template = FOLLOW_UP_TEMPLATE.replace("{value_add}", value_add)
    
    return template


def get_unsubscribe_footer() -> str:
    """
    Get the standard unsubscribe footer.
    
    Returns:
        Unsubscribe text
    """
    return """---
If you'd prefer not to receive further messages, just reply with "unsubscribe" and I won't contact you again."""


def get_signature_template(
    name: str,
    title: str = "",
    phone: str = "",
    email: str = "",
    linkedin: str = "",
) -> str:
    """
    Generate an email signature.
    
    Args:
        name: Full name
        title: Job title
        phone: Phone number
        email: Email address
        linkedin: LinkedIn URL
    
    Returns:
        Formatted signature
    """
    lines = [f"Best regards,", "", name]
    
    if title:
        lines.append(title)
    
    contact_info = []
    if phone:
        contact_info.append(phone)
    if email:
        contact_info.append(email)
    
    if contact_info:
        lines.append(" | ".join(contact_info))
    
    if linkedin:
        lines.append(linkedin)
    
    return "\n".join(lines)


# =============================================================================
# Placeholder Documentation
# =============================================================================

TEMPLATE_PLACEHOLDERS = {
    "recipient_name": "The recipient's first name",
    "company_name": "Target company name",
    "role_title": "Job title being applied for",
    "personalized_hook": "Custom opening based on research",
    "why_interested": "Why you're interested in this specific role/company",
    "relevant_experience": "1-2 sentences of relevant experience",
    "value_proposition": "What you can bring to the role",
    "signature": "Your email signature",
    "unsubscribe": "Unsubscribe footer (required)",
    "days_ago": "Number of days since first email",
    "value_add": "New information or context for follow-up",
    "conversation_type": "Type of conversation (call, interview, etc.)",
    "specific_detail": "Something specific you discussed",
    "contribution": "How you'd contribute to the team",
    "field": "Industry or field of interest",
    "why_reaching_out": "Reason for wanting to connect",
    "connection_context": "How you're connected to the person",
    "recent_accomplishment": "Recent achievement to mention",
}


def get_placeholder_help() -> str:
    """Get documentation for all template placeholders."""
    lines = ["Template Placeholders:", "=" * 40]
    for placeholder, description in TEMPLATE_PLACEHOLDERS.items():
        lines.append(f"{{{placeholder}}}: {description}")
    return "\n".join(lines)

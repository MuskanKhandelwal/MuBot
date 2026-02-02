"""
Memory Data Models

This module defines the data structures used throughout MuBot's memory system.
All models use Pydantic for:
- Type validation
- Serialization/deserialization
- Schema documentation
- IDE autocomplete support

Models are organized by purpose:
- Core memory structures
- Outreach tracking
- User preferences
- Pipeline management
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================

class EmailTone(str, Enum):
    """Available tone styles for cold emails."""
    FORMAL = "formal"      # Polished, traditional, conservative
    FRIENDLY = "friendly"  # Warm, conversational, approachable
    BOLD = "bold"          # Confident, direct, stands out


class ResponseCategory(str, Enum):
    """Classification categories for email responses."""
    POSITIVE = "positive"       # Interested, wants to talk
    NEUTRAL = "neutral"         # Acknowledged, forwarded
    REJECTION = "rejection"     # Not hiring, not interested
    NO_RESPONSE = "no-response" # Automated, out-of-office
    NEEDS_REPLY = "needs-reply" # Asking questions


class OutreachStatus(str, Enum):
    """Status of an outreach attempt."""
    DRAFT = "draft"             # Created but not sent
    SCHEDULED = "scheduled"     # Queued for future send
    SENT = "sent"               # Delivered to recipient
    REPLIED = "replied"         # Received response
    FOLLOWUP_SENT = "followup-sent"  # Follow-up delivered
    CONVERTED = "converted"     # Led to interview/opportunity
    DEAD = "dead"               # No response after max follow-ups


# =============================================================================
# Core Memory Models
# =============================================================================

class MemoryEntry(BaseModel):
    """
    Base model for any memory entry.
    
    All memory entries have:
    - A unique identifier
    - A timestamp
    - Tags for categorization
    - Optional metadata
    """
    id: str = Field(..., description="Unique identifier (UUID)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        # Enable ORM mode for database compatibility
        from_attributes = True


class OutreachEntry(MemoryEntry):
    """
    Records a single cold email outreach attempt.
    
    This is the core tracking entity for job search outreach.
    It captures everything from initial draft through final outcome.
    """
    # Recipient Information
    recipient_email: str
    recipient_name: Optional[str] = None
    recipient_title: Optional[str] = None
    
    # Company & Role Information
    company_name: str
    role_title: str
    job_description_url: Optional[str] = None
    
    # Email Content
    subject: str
    body: str
    personalization_elements: list[str] = Field(default_factory=list)
    
    # Status Tracking
    status: OutreachStatus = OutreachStatus.DRAFT
    response_category: Optional[ResponseCategory] = None
    
    # Timeline
    drafted_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    
    # Follow-up Tracking
    followup_count: int = 0
    max_followups: int = 3
    next_followup_scheduled: Optional[datetime] = None
    
    # Response Content (if received)
    response_body: Optional[str] = None
    extracted_action_items: list[str] = Field(default_factory=list)
    
    # Gmail Integration
    gmail_thread_id: Optional[str] = None
    gmail_message_id: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    
    # A/B Testing
    variant_name: Optional[str] = None  # e.g., "A", "B" for testing
    
    @field_validator("followup_count")
    @classmethod
    def validate_followup_count(cls, v: int) -> int:
        """Ensure follow-up count is non-negative."""
        if v < 0:
            return 0
        return v


class EmailThread(MemoryEntry):
    """
    Represents a conversation thread with a recipient.
    
    Groups multiple outreach entries (initial + follow-ups) into
    a single coherent conversation.
    """
    recipient_email: str
    company_name: str
    role_title: str
    
    # Thread Contents
    entries: list[str] = Field(default_factory=list)  # IDs of OutreachEntries
    
    # Thread Status
    is_active: bool = True
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Outcome
    final_status: Optional[OutreachStatus] = None
    outcome_notes: Optional[str] = None
    
    # Aggregated Metrics
    total_emails_sent: int = 0
    total_replies: int = 0
    days_active: int = 0


class CompanyHistory(BaseModel):
    """
    Aggregated history of all outreach to a specific company.
    
    Prevents duplicate outreach and provides context for personalization.
    """
    company_name: str
    company_domain: Optional[str] = None
    
    # All outreach attempts to this company
    outreach_ids: list[str] = Field(default_factory=list)
    
    # Summary Statistics
    total_outreach: int = 0
    responses_received: int = 0
    positive_responses: int = 0
    rejections: int = 0
    
    # Key Contacts
    contacts_contacted: list[dict] = Field(default_factory=list)
    
    # Learnings
    what_worked: list[str] = Field(default_factory=list)
    what_didnt_work: list[str] = Field(default_factory=list)
    
    # Last Contact
    first_contact_date: Optional[datetime] = None
    last_contact_date: Optional[datetime] = None
    last_status: Optional[str] = None
    
    # Flags
    do_not_contact: bool = False
    do_not_contact_reason: Optional[str] = None


# =============================================================================
# User Profile Models
# =============================================================================

class UserProfile(BaseModel):
    """
    User's professional profile and preferences.
    
    Stored in USER.md and loaded at the start of each session.
    This personalizes the agent's behavior for the specific user.
    """
    # Identity
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "UTC"
    
    # Professional Background
    current_title: Optional[str] = None
    summary: Optional[str] = None
    key_skills: list[str] = Field(default_factory=list)
    years_experience: Optional[int] = None
    
    # Links
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_url: Optional[str] = None
    
    # Preferences
    preferred_tone: EmailTone = EmailTone.FRIENDLY
    email_signature: Optional[str] = None
    
    # Constraints
    max_daily_emails: int = 20
    preferred_send_times: list[str] = Field(default_factory=lambda: ["9:00", "14:00"])
    
    # Goals
    target_roles: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    salary_expectations: Optional[str] = None


class DailyStats(BaseModel):
    """
    Statistics for a single day of outreach activity.
    
    Used for tracking limits and generating reports.
    """
    date: str  # YYYY-MM-DD format
    emails_drafted: int = 0
    emails_sent: int = 0
    replies_received: int = 0
    positive_responses: int = 0
    rejections: int = 0
    followups_sent: int = 0
    
    # Tracking against limits
    emails_sent_today: int = 0
    limit_reached: bool = False


# =============================================================================
# Pipeline Models
# =============================================================================

class JobOpportunity(BaseModel):
    """
    Represents a job opportunity being pursued.
    
    Part of the job search pipeline tracking.
    """
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Job Details
    company_name: str
    role_title: str
    job_description: Optional[str] = None
    job_url: Optional[str] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    
    # Pipeline Stage
    stage: str = "identified"  # identified, applied, phone_screen, interview, offer, rejected
    
    # Relationships
    outreach_entry_ids: list[str] = Field(default_factory=list)
    
    # Notes
    notes: list[dict] = Field(default_factory=list)
    
    # Next Actions
    next_action: Optional[str] = None
    next_action_due: Optional[datetime] = None
    
    # Outcome
    is_active: bool = True
    outcome: Optional[str] = None
    outcome_date: Optional[datetime] = None


# =============================================================================
# Heartbeat State Model
# =============================================================================

class HeartbeatState(BaseModel):
    """
    Persistent state for the heartbeat scheduler.
    
    Stored in heartbeat-state.json and updated on each heartbeat run.
    """
    last_run: Optional[datetime] = None
    next_scheduled_run: Optional[datetime] = None
    
    # Pending Tasks
    scheduled_followups: list[dict] = Field(default_factory=list)
    pending_replies_to_check: list[str] = Field(default_factory=list)
    
    # Campaign State
    campaigns_paused: bool = False
    pause_reason: Optional[str] = None
    pause_until: Optional[datetime] = None
    
    # Rate Limiting
    last_send_timestamp: Optional[datetime] = None
    emails_sent_in_last_hour: int = 0
    
    # Daily Tracking
    current_date: Optional[str] = None  # YYYY-MM-DD
    daily_email_count: int = 0

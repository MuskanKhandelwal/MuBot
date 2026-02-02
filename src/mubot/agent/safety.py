"""
Safety Guardrails Module

This module implements all safety checks and ethical constraints for MuBot.
It ensures the agent operates within defined boundaries and respects user
preferences and recipient rights.

Safety Principles:
1. Explicit Consent: No emails sent without user approval
2. Rate Limiting: Prevent spam-like behavior
3. Privacy Respect: No unauthorized data collection
4. Transparency: Clear labeling of AI-generated content
5. Opt-out Respect: Honor unsubscribe requests immediately

The SafetyGuardrails class provides methods to validate actions before
they are executed, returning detailed results about any violations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from mubot.memory import MemoryManager


class SafetyLevel(Enum):
    """Severity levels for safety violations."""
    INFO = "info"           # Informational, no action needed
    WARNING = "warning"     # Caution advised
    BLOCKING = "blocking"   # Action must not proceed


class ViolationType(Enum):
    """Types of safety violations."""
    RATE_LIMIT = "rate_limit"
    DAILY_LIMIT = "daily_limit"
    DUPLICATE_OUTREACH = "duplicate_outreach"
    NO_CONTACT_LIST = "no_contact_list"
    MISSING_APPROVAL = "missing_approval"
    UNSUBSCRIBE_REQUEST = "unsubscribe_request"
    MASS_EMAIL_PATTERN = "mass_email_pattern"
    MISSING_UNSUBSCRIBE = "missing_unsubscribe"


@dataclass
class SafetyCheck:
    """Result of a safety check."""
    passed: bool
    level: SafetyLevel
    violation_type: Optional[ViolationType]
    message: str
    details: dict


class SafetyGuardrails:
    """
    Enforces safety and ethical constraints on agent actions.
    
    This class is instantiated once per session and used to validate
    all potentially impactful actions before execution.
    
    Usage:
        safety = SafetyGuardrails(memory_manager)
        
        check = safety.can_send_email(
            recipient="hiring@company.com",
            company="TechCorp"
        )
        
        if not check.passed:
            print(f"Blocked: {check.message}")
    """
    
    def __init__(
        self,
        memory: MemoryManager,
        max_daily_emails: int = 20,
        min_interval_seconds: int = 300,
        max_followups: int = 3,
    ):
        """
        Initialize safety guardrails.
        
        Args:
            memory: MemoryManager for checking history
            max_daily_emails: Maximum emails allowed per day
            min_interval_seconds: Minimum time between emails
            max_followups: Maximum follow-ups per thread
        """
        self.memory = memory
        self.max_daily_emails = max_daily_emails
        self.min_interval_seconds = min_interval_seconds
        self.max_followups = max_followups
    
    # ======================================================================
    # Primary Safety Checks
    # ======================================================================
    
    def can_send_email(
        self,
        recipient_email: str,
        company_name: str,
        has_explicit_approval: bool = False,
    ) -> SafetyCheck:
        """
        Comprehensive check before sending any email.
        
        This is the main entry point for send validation. It runs all
        relevant checks and returns a consolidated result.
        
        Args:
            recipient_email: Target email address
            company_name: Company being contacted
            has_explicit_approval: Whether user explicitly approved
        
        Returns:
            SafetyCheck with pass/fail and details
        """
        checks = [
            self._check_approval(has_explicit_approval),
            self._check_daily_limit(),
            self._check_rate_limit(),
            self._check_company_contact(company_name),
            self._check_no_contact_list(recipient_email),
        ]
        
        # Return the most severe failure, or success if all pass
        failures = [c for c in checks if not c.passed]
        if failures:
            # Return the most severe failure (blocking > warning > info)
            blocking = [f for f in failures if f.level == SafetyLevel.BLOCKING]
            if blocking:
                return blocking[0]
            warnings = [f for f in failures if f.level == SafetyLevel.WARNING]
            if warnings:
                return warnings[0]
            return failures[0]
        
        return SafetyCheck(
            passed=True,
            level=SafetyLevel.INFO,
            violation_type=None,
            message="All safety checks passed",
            details={}
        )
    
    def can_schedule_followup(
        self,
        company_name: str,
        followup_count: int,
        last_contact_date: Optional[datetime] = None,
    ) -> SafetyCheck:
        """
        Check if a follow-up can be scheduled.
        
        Args:
            company_name: Company being followed up with
            followup_count: Number of follow-ups already sent
            last_contact_date: When the last email was sent
        
        Returns:
            SafetyCheck result
        """
        # Check follow-up limit
        if followup_count >= self.max_followups:
            return SafetyCheck(
                passed=False,
                level=SafetyLevel.BLOCKING,
                violation_type=ViolationType.MASS_EMAIL_PATTERN,
                message=f"Maximum follow-ups ({self.max_followups}) reached for {company_name}",
                details={
                    "company": company_name,
                    "followups_sent": followup_count,
                    "max_allowed": self.max_followups,
                }
            )
        
        # Check minimum interval since last contact
        if last_contact_date:
            days_since = (datetime.utcnow() - last_contact_date).days
            min_days = 3 if followup_count == 0 else 5
            
            if days_since < min_days:
                return SafetyCheck(
                    passed=False,
                    level=SafetyLevel.WARNING,
                    violation_type=ViolationType.RATE_LIMIT,
                    message=f"Only {days_since} days since last contact. Recommend waiting {min_days} days.",
                    details={
                        "days_since": days_since,
                        "minimum_recommended": min_days,
                        "suggested_date": (last_contact_date + timedelta(days=min_days)).isoformat(),
                    }
                )
        
        return SafetyCheck(
            passed=True,
            level=SafetyLevel.INFO,
            violation_type=None,
            message="Follow-up can be scheduled",
            details={
                "followup_number": followup_count + 1,
                "remaining": self.max_followups - followup_count - 1,
            }
        )
    
    def check_email_content(self, subject: str, body: str) -> SafetyCheck:
        """
        Validate email content for safety issues.
        
        Checks for:
        - Unsubscribe option included
        - No misleading claims
        - Professional tone
        
        Args:
            subject: Email subject line
            body: Email body content
        
        Returns:
            SafetyCheck result
        """
        issues = []
        
        # Check for unsubscribe option
        body_lower = body.lower()
        unsubscribe_indicators = [
            "unsubscribe",
            "opt out",
            "don't want to receive",
            "no longer interested",
        ]
        
        has_unsubscribe = any(ind in body_lower for ind in unsubscribe_indicators)
        
        if not has_unsubscribe:
            issues.append("Email missing unsubscribe/opt-out language")
        
        # Check for spam trigger words (basic check)
        spam_words = ["guaranteed", "act now", "limited time", "winner", "free money"]
        found_spam_words = [w for w in spam_words if w in body_lower]
        
        if found_spam_words:
            issues.append(f"Potentially spammy language detected: {found_spam_words}")
        
        if issues:
            return SafetyCheck(
                passed=False,
                level=SafetyLevel.WARNING,
                violation_type=ViolationType.MISSING_UNSUBSCRIBE,
                message="; ".join(issues),
                details={"issues": issues}
            )
        
        return SafetyCheck(
            passed=True,
            level=SafetyLevel.INFO,
            violation_type=None,
            message="Email content passes safety checks",
            details={}
        )
    
    # ======================================================================
    # Individual Check Methods
    # ======================================================================
    
    def _check_approval(self, has_approval: bool) -> SafetyCheck:
        """Check if user has explicitly approved the send."""
        if not has_approval:
            return SafetyCheck(
                passed=False,
                level=SafetyLevel.BLOCKING,
                violation_type=ViolationType.MISSING_APPROVAL,
                message="Explicit user approval required before sending",
                details={"action_required": "User must confirm send"}
            )
        return SafetyCheck(
            passed=True,
            level=SafetyLevel.INFO,
            violation_type=None,
            message="Approval confirmed",
            details={}
        )
    
    def _check_daily_limit(self) -> SafetyCheck:
        """Check if daily email limit has been reached."""
        stats = self.memory.get_daily_stats()
        
        if stats.emails_sent >= self.max_daily_emails:
            return SafetyCheck(
                passed=False,
                level=SafetyLevel.BLOCKING,
                violation_type=ViolationType.DAILY_LIMIT,
                message=f"Daily limit of {self.max_daily_emails} emails reached",
                details={
                    "sent_today": stats.emails_sent,
                    "limit": self.max_daily_emails,
                    "resets_at": "midnight UTC",
                }
            )
        
        remaining = self.max_daily_emails - stats.emails_sent
        return SafetyCheck(
            passed=True,
            level=SafetyLevel.INFO,
            violation_type=None,
            message=f"{remaining} emails remaining today",
            details={"remaining": remaining, "sent": stats.emails_sent}
        )
    
    def _check_rate_limit(self) -> SafetyCheck:
        """Check if minimum interval between emails has passed."""
        state = self.memory.load_heartbeat_state()
        
        if state.last_send_timestamp:
            elapsed = (datetime.utcnow() - state.last_send_timestamp).total_seconds()
            
            if elapsed < self.min_interval_seconds:
                wait_time = self.min_interval_seconds - elapsed
                return SafetyCheck(
                    passed=False,
                    level=SafetyLevel.WARNING,
                    violation_type=ViolationType.RATE_LIMIT,
                    message=f"Rate limit: Please wait {int(wait_time)} seconds before sending",
                    details={
                        "elapsed_seconds": int(elapsed),
                        "minimum_seconds": self.min_interval_seconds,
                        "wait_seconds": int(wait_time),
                    }
                )
        
        return SafetyCheck(
            passed=True,
            level=SafetyLevel.INFO,
            violation_type=None,
            message="Rate limit check passed",
            details={}
        )
    
    def _check_company_contact(self, company_name: str) -> SafetyCheck:
        """Check for prior contact with this company."""
        history = self.memory.get_company_history(company_name)
        
        if history.total_outreach > 0:
            return SafetyCheck(
                passed=True,  # Allow but warn
                level=SafetyLevel.WARNING,
                violation_type=ViolationType.DUPLICATE_OUTREACH,
                message=f"Prior contact with {company_name} detected ({history.total_outreach} emails)",
                details={
                    "company": company_name,
                    "previous_outreach": history.total_outreach,
                    "last_contact": history.last_contact_date.isoformat() if history.last_contact_date else None,
                    "recommendation": "Review previous emails to avoid duplication",
                }
            )
        
        return SafetyCheck(
            passed=True,
            level=SafetyLevel.INFO,
            violation_type=None,
            message="No prior contact with this company",
            details={}
        )
    
    def _check_no_contact_list(self, email: str) -> SafetyCheck:
        """Check if recipient is on the do-not-contact list."""
        # This would check against a stored list of unsubscribed addresses
        # For now, placeholder implementation
        return SafetyCheck(
            passed=True,
            level=SafetyLevel.INFO,
            violation_type=None,
            message="Not on no-contact list",
            details={}
        )
    
    # ======================================================================
    # Helper Methods
    # ======================================================================
    
    def add_to_no_contact_list(self, email: str, reason: str) -> bool:
        """
        Add an email to the do-not-contact list.
        
        Called when someone unsubscribes or requests no further contact.
        
        Args:
            email: Email address to block
            reason: Why they were added (unsubscribe, bounce, etc.)
        
        Returns:
            True if added successfully
        """
        # TODO: Implement persistent storage of no-contact list
        return True
    
    def is_mass_email_pattern(self, emails: list[dict]) -> SafetyCheck:
        """
        Detect if a batch of emails looks like mass blasting.
        
        Args:
            emails: List of email dicts with subject and body
        
        Returns:
            SafetyCheck result
        """
        if len(emails) > 10:
            return SafetyCheck(
                passed=False,
                level=SafetyLevel.BLOCKING,
                violation_type=ViolationType.MASS_EMAIL_PATTERN,
                message=f"Batch of {len(emails)} emails detected. Send in smaller batches.",
                details={"batch_size": len(emails), "max_recommended": 10}
            )
        
        # Check for identical content
        subjects = [e.get("subject", "") for e in emails]
        if len(set(subjects)) < len(subjects) * 0.5:
            return SafetyCheck(
                passed=False,
                level=SafetyLevel.WARNING,
                violation_type=ViolationType.MASS_EMAIL_PATTERN,
                message="Many emails have identical subjects. Consider more personalization.",
                details={"unique_subjects": len(set(subjects)), "total": len(subjects)}
            )
        
        return SafetyCheck(
            passed=True,
            level=SafetyLevel.INFO,
            violation_type=None,
            message="Email batch passes pattern checks",
            details={}
        )

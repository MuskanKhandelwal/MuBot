"""
Core Agent Module

The JobSearchAgent is the main orchestrator that coordinates all components
of MuBot. It provides a high-level interface for users to interact with
the system while managing the complexity of:
- Memory management
- Safety validation
- LLM reasoning
- Tool execution
- State tracking

The agent follows a structured workflow (the REACT pattern):
1. Receive: Accept user input
2. Recall: Load relevant memory and context
3. Reason: Plan approach using LLM
4. Check: Validate safety constraints
5. Act: Execute approved actions
6. Learn: Update memory with outcomes
"""

import asyncio
from datetime import datetime, timedelta
from typing import AsyncIterator, Optional

from mubot.agent.reasoning import ReasoningEngine
from mubot.agent.safety import SafetyGuardrails, SafetyCheck, SafetyLevel
from mubot.config import get_settings
from mubot.config.prompts import DAILY_SUMMARY_PROMPT, MEMORY_UPDATE_PROMPT
from mubot.memory import MemoryManager
from mubot.memory.models import (
    OutreachEntry,
    OutreachStatus,
    ResponseCategory,
    UserProfile,
)
from mubot.tools.gmail_client import GmailClient


class JobSearchAgent:
    """
    Main orchestrator for the job search cold emailing system.
    
    This is the primary interface that users interact with. It coordinates
    all subsystems to provide a seamless experience for:
    - Drafting personalized cold emails
    - Managing outreach campaigns
    - Tracking responses and follow-ups
    - Learning from outcomes
    
    Usage:
        agent = JobSearchAgent()
        await agent.initialize()
        
        # Draft an email
        draft = await agent.draft_email(
            company_name="TechCorp",
            role_title="Senior Engineer",
            # ...
        )
        
        # Send after user approval
        await agent.send_email(draft, approved=True)
    """
    
    def __init__(self, memory_path: Optional[str] = None):
        """
        Initialize the job search agent.
        
        Args:
            memory_path: Path to memory directory (default: ./data)
        """
        self.settings = get_settings()
        self.memory_path = memory_path or str(self.settings.memory_base_path)
        
        # Initialize subsystems
        self.memory = MemoryManager(self.memory_path)
        self.safety = SafetyGuardrails(
            memory=self.memory,
            max_daily_emails=self.settings.max_daily_emails,
            min_interval_seconds=self.settings.min_email_interval_seconds,
            max_followups=self.settings.max_followups,
        )
        self.reasoning = ReasoningEngine(self.settings)
        
        # Session state
        self.user_profile: Optional[UserProfile] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize the agent by loading user profile and memory.
        
        This should be called before using the agent to ensure all
        context is loaded.
        
        Returns:
            True if initialization successful
        """
        # Load user profile
        self.user_profile = self.memory.load_user_profile()
        
        if self.user_profile is None:
            print("⚠️  No USER.md found. Run initialization to create one.")
            return False
        
        self._initialized = True
        return True
    
    # ======================================================================
    # Email Operations
    # ======================================================================
    
    async def draft_email(
        self,
        company_name: str,
        role_title: str,
        company_context: str = "",
        job_description: str = "",
        recipient_name: Optional[str] = None,
        recipient_email: Optional[str] = None,
        recipient_title: Optional[str] = None,
    ) -> tuple[OutreachEntry, list[str]]:
        """
        Draft a personalized cold email.
        
        This method:
        1. Loads company history from memory
        2. Generates personalized content via LLM
        3. Checks for safety issues
        4. Saves draft to memory
        
        Args:
            company_name: Target company name
            role_title: Job title
            company_context: Context about the company
            job_description: Job description or posting
            recipient_name: Recipient's name
            recipient_email: Recipient's email address
            recipient_title: Recipient's job title
        
        Returns:
            Tuple of (OutreachEntry draft, list of warnings)
        """
        if not self._initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        # Load company history for context
        company_history = self.memory.get_company_history(company_name)
        history_text = ""
        if company_history.total_outreach > 0:
            history_text = f"Previous contact: {company_history.total_outreach} emails. "
            history_text += f"Last contact: {company_history.last_contact_date or 'unknown'}. "
            history_text += f"Responses: {company_history.responses_received}"
        
        # Generate draft via reasoning engine
        draft = await self.reasoning.draft_email(
            user_profile=self.user_profile,
            company_name=company_name,
            role_title=role_title,
            company_context=company_context,
            job_description=job_description,
            recipient_name=recipient_name,
            recipient_title=recipient_title,
            company_history=history_text,
        )
        
        # Set recipient email if provided
        if recipient_email:
            draft.recipient_email = recipient_email
        
        # Safety check on content
        warnings = []
        content_check = self.safety.check_email_content(draft.subject, draft.body)
        if not content_check.passed:
            warnings.append(f"Content check: {content_check.message}")
        
        # Check company history for duplicate outreach
        company_check = self.safety.can_send_email(
            recipient_email=draft.recipient_email or "",
            company_name=company_name,
            has_explicit_approval=False,  # Just checking, not sending
        )
        if company_check.violation_type and company_check.level != SafetyLevel.INFO:
            warnings.append(f"Company check: {company_check.message}")
        
        # Save draft to memory
        self.memory.save_outreach_entry(draft)
        
        return draft, warnings
    
    async def send_email(
        self,
        entry: OutreachEntry,
        approved: bool = False,
        attachments: Optional[list[str]] = None,
    ) -> tuple[bool, str]:
        """
        Send an email after safety validation.
        
        Args:
            entry: OutreachEntry to send
            approved: Whether user has explicitly approved
            attachments: Optional list of file paths to attach
        
        Returns:
            Tuple of (success, message)
        """
        if not self._initialized:
            return False, "Agent not initialized"
        
        # Run safety checks
        safety_result = self.safety.can_send_email(
            recipient_email=entry.recipient_email,
            company_name=entry.company_name,
            has_explicit_approval=approved,
        )
        
        if not safety_result.passed:
            return False, f"Safety check failed: {safety_result.message}"
        
        if not approved:
            return False, "Explicit user approval required. Set approved=True to send."
        
        # Actually send via Gmail
        gmail = GmailClient(self.settings)
        authenticated = await gmail.authenticate()
        
        if not authenticated:
            return False, "Gmail authentication failed. Please check your credentials."
        
        # Combine entry attachments with passed attachments
        all_attachments = list(entry.attachments or [])
        if attachments:
            all_attachments.extend(attachments)
        
        message_id = await gmail.send_email(
            to=entry.recipient_email,
            subject=entry.subject,
            body=entry.body.replace('\n', '<br>'),  # Convert to HTML
            thread_id=entry.gmail_thread_id,
            apply_label=True,
            attachments=all_attachments if all_attachments else None,
        )
        
        if not message_id:
            return False, "Failed to send email via Gmail"
        
        # Update entry with Gmail info
        entry.gmail_message_id = message_id
        entry.status = OutreachStatus.SENT
        entry.sent_at = datetime.utcnow()
        
        # Save updated entry
        self.memory.save_outreach_entry(entry)
        
        # Update heartbeat state
        state = self.memory.load_heartbeat_state()
        state.last_send_timestamp = datetime.utcnow()
        state.daily_email_count += 1
        self.memory.save_heartbeat_state(state)
        
        return True, f"Email sent to {entry.recipient_email}"
    
    async def schedule_followup(
        self,
        entry: OutreachEntry,
        days_delay: Optional[int] = None,
    ) -> tuple[bool, str]:
        """
        Schedule a follow-up email.
        
        Args:
            entry: Original outreach entry
            days_delay: Days to wait (default: from settings)
        
        Returns:
            Tuple of (success, message)
        """
        days_delay = days_delay or self.settings.default_followup_delay_days
        
        # Check if follow-up is allowed
        check = self.safety.can_schedule_followup(
            company_name=entry.company_name,
            followup_count=entry.followup_count,
            last_contact_date=entry.sent_at,
        )
        
        if not check.passed:
            return False, check.message
        
        # Calculate scheduled time
        scheduled_time = datetime.utcnow() + timedelta(days=days_delay)
        entry.next_followup_scheduled = scheduled_time
        
        # Add to heartbeat state
        state = self.memory.load_heartbeat_state()
        state.scheduled_followups.append({
            "entry_id": entry.id,
            "due_at": scheduled_time.isoformat(),
            "company": entry.company_name,
            "followup_number": entry.followup_count + 1,
        })
        self.memory.save_heartbeat_state(state)
        
        return True, f"Follow-up scheduled for {scheduled_time.isoformat()}"
    
    # ======================================================================
    # Response Handling
    # ======================================================================
    
    async def process_response(
        self,
        entry: OutreachEntry,
        response_body: str,
    ) -> tuple[ResponseCategory, dict]:
        """
        Process an incoming email response.
        
        Args:
            entry: Original outreach entry
            response_body: Response content
        
        Returns:
            Tuple of (category, extracted_data)
        """
        # Classify the response
        category, data = await self.reasoning.classify_response(entry, response_body)
        
        # Update entry
        entry.status = OutreachStatus.REPLIED
        entry.response_category = category
        entry.response_body = response_body
        entry.replied_at = datetime.utcnow()
        
        # Clear any scheduled follow-up
        entry.next_followup_scheduled = None
        
        # Save to memory
        self.memory.save_outreach_entry(entry)
        
        # Update heartbeat state (remove from pending follow-ups)
        state = self.memory.load_heartbeat_state()
        state.scheduled_followups = [
            f for f in state.scheduled_followups 
            if f.get("entry_id") != entry.id
        ]
        self.memory.save_heartbeat_state(state)
        
        return category, data
    
    # ======================================================================
    # Query and Summary
    # ======================================================================
    
    async def get_daily_summary(self) -> str:
        """
        Generate a summary of today's activity.
        
        Returns:
            Formatted summary string
        """
        stats = self.memory.get_daily_stats()
        
        # TODO: Load actual data for comprehensive summary
        summary_data = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "emails_sent": stats.emails_sent,
            "replies_received": stats.replies_received,
            "positive_responses": stats.positive_responses,
            "rejections": stats.rejections,
            "pipeline_changes": "No updates",
            "scheduled_followups": "3 pending",
        }
        
        # Use LLM to generate nice summary
        prompt = DAILY_SUMMARY_PROMPT.format(**summary_data)
        
        messages = [
            {"role": "system", "content": "You are a helpful job search assistant."},
            {"role": "user", "content": prompt},
        ]
        
        return await self.reasoning._generate(messages, temperature=0.7)
    
    def get_company_context(self, company_name: str) -> dict:
        """
        Get all known context about a company.
        
        Args:
            company_name: Company to look up
        
        Returns:
            Dictionary with history, previous contacts, etc.
        """
        history = self.memory.get_company_history(company_name)
        
        return {
            "company_name": history.company_name,
            "total_outreach": history.total_outreach,
            "responses_received": history.responses_received,
            "last_contact": history.last_contact_date,
            "do_not_contact": history.do_not_contact,
            "what_worked": history.what_worked,
        }
    
    # ======================================================================
    # Campaign Management
    # ======================================================================
    
    def pause_campaign(self, reason: str = "User requested") -> bool:
        """
        Pause all outbound email activity.
        
        Args:
            reason: Why the campaign is being paused
        
        Returns:
            True if paused successfully
        """
        state = self.memory.load_heartbeat_state()
        state.campaigns_paused = True
        state.pause_reason = reason
        state.pause_until = None  # Indefinite
        return self.memory.save_heartbeat_state(state)
    
    def resume_campaign(self) -> bool:
        """
        Resume outbound email activity.
        
        Returns:
            True if resumed successfully
        """
        state = self.memory.load_heartbeat_state()
        state.campaigns_paused = False
        state.pause_reason = None
        state.pause_until = None
        return self.memory.save_heartbeat_state(state)
    
    def is_campaign_paused(self) -> tuple[bool, Optional[str]]:
        """
        Check if campaigns are currently paused.
        
        Returns:
            Tuple of (is_paused, reason)
        """
        state = self.memory.load_heartbeat_state()
        return state.campaigns_paused, state.pause_reason


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """
    Main entry point for running the agent.
    
    This is called when running `mubot` from the command line.
    """
    import sys
    
    print("=" * 60)
    print("🤖 MuBot - Job Search Cold Emailing Agent")
    print("=" * 60)
    print()
    print("Available commands:")
    print()
    print("  mubot-init       - Initialize MuBot (run this first!)")
    print("  mubot-chat       - Start interactive chat mode")
    print("  mubot-heartbeat  - Run scheduled tasks")
    print()
    print("Or use in your Python code:")
    print()
    print("    import asyncio")
    print("    from agent import JobSearchAgent")
    print()
    print("    async def main():")
    print("        agent = JobSearchAgent()")
    print("        await agent.initialize()")
    print()
    print("        # Draft an email")
    print("        draft, warnings = await agent.draft_email(")
    print("            company_name='Example Corp',")
    print("            role_title='Senior Engineer',")
    print("        )")
    print()
    print("    asyncio.run(main())")
    print()
    
    # Offer to start chat mode
    try:
        response = input("Would you like to start the interactive chat? (y/n): ")
        if response.lower().strip() in ['y', 'yes']:
            print("\nStarting chat mode...\n")
            # Import and run cli
            from cli import main as cli_main
            asyncio.run(cli_main())
            return
    except (EOFError, KeyboardInterrupt):
        pass
    
    print("\nFirst time? Run `mubot-init` to set up your profile.")
    print("Then run `mubot-chat` to start the interactive chat.")


if __name__ == "__main__":
    main()

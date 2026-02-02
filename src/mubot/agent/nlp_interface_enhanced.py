"""
Enhanced Natural Language Interface with Job Description Support

This extends the base NLExecutor to support multi-turn conversations
for collecting job descriptions and other details.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from mubot.agent.nlp_interface import NLExecutor, IntentType, ParsedIntent, IntentParser
from mubot.agent.reasoning import ReasoningEngine
from mubot.config.settings import Settings


class ConversationState(Enum):
    """States for multi-turn conversation."""
    IDLE = "idle"
    COLLECTING_JD = "collecting_jd"  # Waiting for job description
    COLLECTING_RECIPIENT = "collecting_recipient"
    CONFIRMING_SEND = "confirming_send"
    COLLECTING_COMPANY_DETAILS = "collecting_company_details"


@dataclass
class DraftInProgress:
    """Stores draft state during multi-turn conversation."""
    company_name: str = ""
    role_title: str = ""
    job_description: str = ""
    company_context: str = ""
    recipient_name: str = ""
    recipient_title: str = ""
    recipient_email: str = ""
    use_jd_enhanced: bool = False
    collected_fields: list = field(default_factory=list)


class EnhancedNLExecutor(NLExecutor):
    """
    Enhanced executor with multi-turn conversation support.
    
    This allows collecting information over multiple messages,
    especially useful for pasting long job descriptions.
    """
    
    def __init__(self, agent):
        super().__init__(agent)
        self.state = ConversationState.IDLE
        self.draft_in_progress: Optional[DraftInProgress] = None
        self._pending_jd_lines: list = []
    
    async def execute(self, user_input: str) -> str:
        """
        Parse and execute a natural language command.
        
        Handles multi-turn conversations for complex tasks.
        """
        # Check if we're in a multi-turn conversation
        if self.state == ConversationState.COLLECTING_JD:
            return await self._handle_jd_input(user_input)
        
        if self.state == ConversationState.COLLECTING_RECIPIENT:
            return await self._handle_recipient_input(user_input)
        
        if self.state == ConversationState.CONFIRMING_SEND:
            return await self._handle_confirmation_input(user_input)
        
        # Normal single-turn processing
        intent = await self.parser.parse(user_input)
        
        # Handle simple commands that don't need NLP parsing
        user_input_lower = user_input.lower().strip()
        
        # Check follow-ups command
        if any(phrase in user_input_lower for phrase in ['check follow', 'pending follow', 'show follow', 'list follow']):
            return await self._handle_check_followups()
        
        # Special handling for DRAFT_EMAIL - use multi-turn flow
        if intent.intent == IntentType.DRAFT_EMAIL:
            return await self._handle_draft_email_enhanced(intent, user_input)
        
        # Special handling for SEND_EMAIL when we have a last draft
        if intent.intent == IntentType.SEND_EMAIL:
            return await self._handle_send_email_quick()
        
        # For other intents, check if clarification is needed
        if intent.clarification_needed:
            return f"🤔 {intent.clarification_question}"
        
        # Use parent class handlers for other intents
        return await self._route_to_handler(intent)
    
    async def _handle_draft_email_enhanced(self, intent: ParsedIntent, raw_input: str) -> str:
        """
        Handle draft email with JD support.
        
        Always starts multi-turn collection for best results.
        """
        params = intent.params
        
        if not params.get("company_name"):
            return "❌ I need to know which company. Try: 'Draft an email for the engineer role at Google'"
        
        # Check if JD was included in the command
        jd_keywords = ["jd", "job description", "posting", "requirements", "responsibilities"]
        has_jd_in_input = any(kw in raw_input.lower() for kw in jd_keywords)
        
        # Initialize draft state
        self.draft_in_progress = DraftInProgress(
            company_name=params.get("company_name"),
            role_title=params.get("role_title", "Software Engineer"),
            recipient_name=params.get("recipient_name", ""),
            recipient_title=params.get("recipient_title", ""),
            recipient_email=params.get("recipient_email", ""),
            use_jd_enhanced=True,  # Always use JD-enhanced for better results
        )
        
        # Always start JD collection for best results
        self.state = ConversationState.COLLECTING_JD
        self._pending_jd_lines = []
        
        return f"""📝 Let's draft an email for **{self.draft_in_progress.role_title}** at **{self.draft_in_progress.company_name}**!

I can create a JD-optimized email that matches your profile to the job requirements.

Please paste the **job description** below. Include:
• Requirements
• Responsibilities  
• Preferred qualifications
• Company/team info

Type **DONE** when finished, or **SKIP** to draft without JD."""
    
    async def _handle_jd_input(self, user_input: str) -> str:
        """Handle job description input during multi-turn conversation."""
        user_input_stripped = user_input.strip()
        
        # Check for completion
        if user_input_stripped.upper() in ["DONE", "END", "FINISHED"]:
            self.state = ConversationState.COLLECTING_RECIPIENT
            
            # Combine JD lines
            full_jd = "\n".join(self._pending_jd_lines)
            self.draft_in_progress.job_description = full_jd
            
            jd_preview = full_jd[:200] + "..." if len(full_jd) > 200 else full_jd
            
            return f"""✅ Job description received! ({len(full_jd)} characters)

Preview: {jd_preview}

Now let's add recipient details:
• Name (e.g., "Sarah Chen")
• Title (e.g., "Engineering Manager")
• Email (optional for now)

**Format:** Name, Title, Email
**Example:** Sarah Chen, Engineering Manager, sarah@company.com

Or type **SKIP** to use "Hiring Manager"."""
        
        # Check for skip
        if user_input_stripped.upper() == "SKIP":
            self.state = ConversationState.COLLECTING_RECIPIENT
            return """⏭️  Skipping JD.

Let's add recipient details:
• Name (e.g., "Sarah Chen")
• Title (e.g., "Engineering Manager")
• Email (optional)

**Format:** Name, Title, Email
Or type **SKIP** to use "Hiring Manager"."""
        
        # Accumulate JD lines
        self._pending_jd_lines.append(user_input)
        
        # Show progress
        line_count = len(self._pending_jd_lines)
        char_count = sum(len(line) for line in self._pending_jd_lines)
        
        if line_count % 5 == 0:  # Update every 5 lines
            return f"📥 Received {line_count} lines ({char_count} chars)... Keep pasting or type **DONE**"
        
        return ""  # Silent accumulation
    
    async def _handle_recipient_input(self, user_input: str) -> str:
        """Handle recipient details input."""
        user_input_stripped = user_input.strip()
        
        # If we're in send flow (no draft_in_progress), just collect email
        if not self.draft_in_progress and hasattr(self, '_last_draft') and self._last_draft:
            if "@" in user_input_stripped:
                self._last_draft.recipient_email = user_input_stripped
                self.state = ConversationState.IDLE
                return f"✅ Email added: {user_input_stripped}\n\nType **send** to send the email."
            else:
                return "❌ Please provide a valid email address (e.g., name@company.com)"
        
        if user_input_stripped.upper() == "SKIP":
            # Use defaults
            self.draft_in_progress.recipient_name = "Hiring Manager"
            self.draft_in_progress.recipient_title = "Manager"
        else:
            # Parse recipient info
            parts = [p.strip() for p in user_input_stripped.split(",")]
            
            if len(parts) >= 1:
                self.draft_in_progress.recipient_name = parts[0]
            if len(parts) >= 2:
                self.draft_in_progress.recipient_title = parts[1]
            if len(parts) >= 3:
                self.draft_in_progress.recipient_email = parts[2]
        
        # Now draft the email
        self.state = ConversationState.IDLE
        
        return await self._create_draft()
    
    async def _handle_send_email_quick(self) -> str:
        """Handle quick send command after drafting."""
        # Check if we have a last draft
        if not hasattr(self, '_last_draft') or not self._last_draft:
            return "❌ No email to send. Draft one first with: 'Draft an email for...'"
        
        entry = self._last_draft
        
        # Check if we have recipient email
        if not entry.recipient_email:
            self.state = ConversationState.COLLECTING_RECIPIENT
            return "📧 Please provide the recipient email address:"
        
        # Show confirmation
        self.state = ConversationState.CONFIRMING_SEND
        return f"""🚀 Ready to send!

**To:** {entry.recipient_name} <{entry.recipient_email}>
**Subject:** {entry.subject}

Type **yes** to confirm sending, or **no** to cancel."""
    
    async def _create_draft(self) -> str:
        """Create the final draft using collected information."""
        draft_data = self.draft_in_progress
        
        if not draft_data:
            return "❌ Something went wrong. Please try again."
        
        # Choose drafting method based on whether JD was provided
        if draft_data.job_description and draft_data.use_jd_enhanced:
            # Use JD-enhanced version
            draft = await self.agent.reasoning.draft_email_with_jd(
                user_profile=self.agent.user_profile,
                company_name=draft_data.company_name,
                role_title=draft_data.role_title,
                job_description=draft_data.job_description,
                company_context=f"{draft_data.company_name} - based on JD analysis",
                recipient_name=draft_data.recipient_name or "Hiring Manager",
                recipient_title=draft_data.recipient_title,
            )
            method_note = "🎯 JD-Enhanced Draft"
        else:
            # Use regular version
            draft, warnings = await self.agent.draft_email(
                company_name=draft_data.company_name,
                role_title=draft_data.role_title,
                job_description=draft_data.job_description,
                company_context=f"{draft_data.company_name} - innovative company",
                recipient_name=draft_data.recipient_name or "Hiring Manager",
                recipient_title=draft_data.recipient_title,
                recipient_email=draft_data.recipient_email,
            )
            method_note = "✉️  Standard Draft"
            warnings = warnings or []
        
        # Set email if provided
        if draft_data.recipient_email:
            draft.recipient_email = draft_data.recipient_email
        
        # Format response
        response = f"""{method_note}

**To:** {draft.recipient_name} <{draft.recipient_email or 'Not set'}>
**Subject:** {draft.subject}

**Body:**
```
{draft.body}
```

**Personalization Elements:**
"""
        
        if draft.personalization_elements:
            for elem in draft.personalization_elements:
                response += f"  • {elem}\n"
        else:
            response += "  • AI-optimized based on your profile\n"
        
        # Store for later
        self._last_draft = draft
        self.draft_in_progress = None
        
        response += """
💡 **Next steps:**
• Type **'send'** to send (I'll ask for confirmation)
• Type **'add email'** to add recipient email
• Type **'redraft'** to try again with different info
"""
        
        return response
    
    async def _handle_check_followups(self) -> str:
        """Check pending follow-ups."""
        pending = self.agent.memory.get_pending_followups()
        
        if not pending:
            return "📅 No pending follow-ups. You're all caught up!"
        
        response = f"📅 **Pending Follow-ups ({len(pending)})**\n\n"
        
        now = datetime.utcnow()
        
        for i, task in enumerate(pending[:10], 1):  # Show max 10
            company = task.get('company', 'Unknown')
            due_str = task.get('due_at', '')
            followup_num = task.get('followup_number', 1)
            
            # Parse due date
            try:
                due_date = datetime.fromisoformat(due_str.replace('Z', '+00:00'))
                if due_date <= now:
                    status = "⚠️ DUE NOW"
                else:
                    days_until = (due_date - now).days
                    if days_until == 0:
                        status = "📅 Today"
                    elif days_until == 1:
                        status = "📅 Tomorrow"
                    else:
                        status = f"📅 In {days_until} days"
            except:
                status = "📅 Scheduled"
            
            response += f"{i}. **{company}** - Follow-up #{followup_num}\n"
            response += f"   Status: {status}\n\n"
        
        if len(pending) > 10:
            response += f"... and {len(pending) - 10} more\n\n"
        
        response += """💡 **Commands:**
• "Send [company] follow-up" - Send now
• "Cancel follow-up for [company]" - Cancel
• "Reschedule [company] to [date]" - Change date"""
        
        return response
    
    async def _route_to_handler(self, intent: ParsedIntent) -> str:
        """Route to appropriate handler (from parent class)."""
        handlers = {
            IntentType.DRAFT_EMAIL: super()._handle_draft_email,
            IntentType.SEND_EMAIL: super()._handle_send_email,
            IntentType.SCHEDULE_FOLLOWUP: super()._handle_schedule_followup,
            IntentType.CHECK_REPLIES: super()._handle_check_replies,
            IntentType.ADD_OPPORTUNITY: super()._handle_add_opportunity,
            IntentType.UPDATE_STAGE: super()._handle_update_stage,
            IntentType.GET_SUMMARY: super()._handle_get_summary,
            IntentType.LIST_PIPELINE: super()._handle_list_pipeline,
            IntentType.PAUSE_CAMPAIGN: super()._handle_pause_campaign,
            IntentType.RESUME_CAMPAIGN: super()._handle_resume_campaign,
            IntentType.GET_COMPANY_INFO: super()._handle_company_info,
            IntentType.HELP: super()._handle_help,
            IntentType.UNKNOWN: super()._handle_unknown,
        }
        
        handler = handlers.get(intent.intent, super()._handle_unknown)
        return await handler(intent)
    
    async def _handle_confirmation_input(self, user_input: str) -> str:
        """Handle send confirmation."""
        user_input_lower = user_input.lower().strip()
        
        if user_input_lower in ["yes", "y", "send", "ok"]:
            if hasattr(self, '_last_draft') and self._last_draft:
                entry = self._last_draft
                success, msg = await self.agent.send_email(entry, approved=True)
                self.state = ConversationState.IDLE
                return f"{'✅' if success else '❌'} {msg}"
            return "❌ No email to send."
        
        elif user_input_lower in ["no", "n", "cancel"]:
            self.state = ConversationState.IDLE
            return "❌ Send cancelled. You can edit and try again."
        
        return "Please type **yes** to send or **no** to cancel."
    
    async def handle_confirmation(self, user_input: str) -> str:
        """
        Handle yes/no confirmation responses and special commands.
        
        Extended to handle draft-related commands.
        """
        user_input_lower = user_input.lower().strip()
        
        # Handle add email command
        if user_input_lower == "add email":
            if hasattr(self, '_last_draft') and self._last_draft:
                self.state = ConversationState.COLLECTING_RECIPIENT
                return "Please provide the recipient email:"
            return "❌ No draft to add email to."
        
        if user_input_lower == "redraft":
            self.draft_in_progress = None
            self.state = ConversationState.IDLE
            return "🔄 Let's start over. What company and role?"
        
        # Check for pending send (from parent)
        return await super().handle_confirmation(user_input)

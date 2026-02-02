"""
Natural Language Interface for MuBot

This module provides natural language understanding for MuBot,
converting user input into structured actions that the agent can execute.

Supported intents:
- draft_email: "Draft a cold email for the senior engineer role at Stripe"
- send_email: "Send the email to Sarah"
- schedule_followup: "Schedule a follow-up in 5 days"
- check_replies: "Check if anyone replied"
- add_opportunity: "Add Meta to my pipeline"
- update_stage: "Move Stripe to interview stage"
- get_summary: "Show me my daily summary"
- list_pipeline: "What's in my pipeline?"
- pause_campaign: "Pause all emails"
- help: "What can you do?"
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from mubot.agent.reasoning import ReasoningEngine
from mubot.config.settings import Settings


class IntentType(Enum):
    """Types of intents the user can express."""
    DRAFT_EMAIL = "draft_email"
    SEND_EMAIL = "send_email"
    SCHEDULE_FOLLOWUP = "schedule_followup"
    CHECK_REPLIES = "check_replies"
    ADD_OPPORTUNITY = "add_opportunity"
    UPDATE_STAGE = "update_stage"
    GET_SUMMARY = "get_summary"
    LIST_PIPELINE = "list_pipeline"
    PAUSE_CAMPAIGN = "pause_campaign"
    RESUME_CAMPAIGN = "resume_campaign"
    GET_COMPANY_INFO = "get_company_info"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Structured representation of user intent."""
    intent: IntentType
    confidence: float
    params: dict
    raw_input: str
    clarification_needed: bool = False
    clarification_question: Optional[str] = None


class IntentParser:
    """
    Parses natural language input into structured intents.
    
    Uses LLM to understand user requests and extract parameters.
    """
    
    SYSTEM_PROMPT = """You are MuBot's natural language parser. Your job is to understand what the user wants to do and extract relevant parameters.

Available actions:
1. draft_email - Draft a cold email
   Parameters: company_name, role_title, recipient_name, recipient_title, recipient_email, company_context

2. send_email - Send a drafted email
   Parameters: entry_id or recipient_name or company_name

3. schedule_followup - Schedule a follow-up email
   Parameters: company_name or entry_id, days_delay (default: 5)

4. check_replies - Check for email replies
   Parameters: company_name (optional, to filter)

5. add_opportunity - Add a job opportunity to pipeline
   Parameters: company_name, role_title, job_url, notes

6. update_stage - Move opportunity to different stage
   Parameters: company_name, new_stage (identified, contacted, applied, interview, offer, rejected)

7. get_summary - Get daily/weekly summary
   Parameters: period (today, week)

8. list_pipeline - Show current pipeline
   Parameters: status (active, all)

9. pause_campaign - Pause all outbound emails
   Parameters: reason

10. resume_campaign - Resume outbound emails
    Parameters: none

11. get_company_info - Get info about past outreach to a company
    Parameters: company_name

12. help - Show available commands
    Parameters: none

Response format (JSON only):
{
    "intent": "intent_name",
    "confidence": 0.95,
    "params": {
        "param1": "value1",
        "param2": "value2"
    },
    "clarification_needed": false,
    "clarification_question": null
}

If you're unsure about any parameter, set clarification_needed to true and ask a specific question.
"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.reasoning = ReasoningEngine(self.settings)
    
    async def parse(self, user_input: str) -> ParsedIntent:
        """
        Parse natural language input into structured intent.
        
        Args:
            user_input: Raw user input
        
        Returns:
            ParsedIntent with extracted parameters
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse this request: \"{user_input}\""}
        ]
        
        try:
            response = await self.reasoning._generate(
                messages,
                temperature=0.3,  # Low temp for consistent parsing
                max_tokens=500
            )
            
            # Extract JSON from response
            parsed = self._extract_json(response)
            
            return ParsedIntent(
                intent=IntentType(parsed.get("intent", "unknown")),
                confidence=parsed.get("confidence", 0.0),
                params=parsed.get("params", {}),
                raw_input=user_input,
                clarification_needed=parsed.get("clarification_needed", False),
                clarification_question=parsed.get("clarification_question")
            )
            
        except Exception as e:
            print(f"Error parsing intent: {e}")
            return ParsedIntent(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                params={},
                raw_input=user_input,
                clarification_needed=True,
                clarification_question="I'm not sure what you'd like to do. Could you rephrase that?"
            )
    
    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response."""
        # Try to find JSON block
        import re
        
        # Look for JSON in code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        # Or just find curly braces
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        
        return json.loads(text)


class NLExecutor:
    """
    Executes parsed intents using the JobSearchAgent.
    
    This is the bridge between natural language and agent actions.
    """
    
    def __init__(self, agent):
        self.agent = agent
        self.parser = IntentParser(agent.settings)
    
    async def execute(self, user_input: str) -> str:
        """
        Parse and execute a natural language command.
        
        Args:
            user_input: Natural language input
        
        Returns:
            Response to show the user
        """
        # Parse the intent
        intent = await self.parser.parse(user_input)
        
        # Check if we need clarification
        if intent.clarification_needed:
            return f"🤔 {intent.clarification_question}"
        
        # Route to appropriate handler
        handlers = {
            IntentType.DRAFT_EMAIL: self._handle_draft_email,
            IntentType.SEND_EMAIL: self._handle_send_email,
            IntentType.SCHEDULE_FOLLOWUP: self._handle_schedule_followup,
            IntentType.CHECK_REPLIES: self._handle_check_replies,
            IntentType.ADD_OPPORTUNITY: self._handle_add_opportunity,
            IntentType.UPDATE_STAGE: self._handle_update_stage,
            IntentType.GET_SUMMARY: self._handle_get_summary,
            IntentType.LIST_PIPELINE: self._handle_list_pipeline,
            IntentType.PAUSE_CAMPAIGN: self._handle_pause_campaign,
            IntentType.RESUME_CAMPAIGN: self._handle_resume_campaign,
            IntentType.GET_COMPANY_INFO: self._handle_company_info,
            IntentType.HELP: self._handle_help,
            IntentType.UNKNOWN: self._handle_unknown,
        }
        
        handler = handlers.get(intent.intent, self._handle_unknown)
        return await handler(intent)
    
    async def _handle_draft_email(self, intent: ParsedIntent) -> str:
        """Handle draft_email intent."""
        params = intent.params
        
        # Validate required params
        if not params.get("company_name"):
            return "❌ I need to know which company. Try: 'Draft an email for the engineer role at Google'"
        
        # Draft the email
        draft, warnings = await self.agent.draft_email(
            company_name=params.get("company_name"),
            role_title=params.get("role_title", "Software Engineer"),
            company_context=params.get("company_context", ""),
            job_description=params.get("job_description", ""),
            recipient_name=params.get("recipient_name"),
            recipient_email=params.get("recipient_email"),
            recipient_title=params.get("recipient_title"),
        )
        
        # Format response
        response = f"""✉️  Drafted email for {params.get('company_name')}!

**Subject:** {draft.subject}

**Body:**
{draft.body}

**Personalization:**
"""
        for elem in draft.personalization_elements:
            response += f"  • {elem}\n"
        
        if warnings:
            response += "\n⚠️  **Warnings:**\n"
            for w in warnings:
                response += f"  • {w}\n"
        
        response += f"\n💡 **To send:** Type 'send the email to {params.get('recipient_name') or params.get('company_name')}' after reviewing"
        
        # Store draft reference for later
        self._last_draft = draft
        
        return response
    
    async def _handle_send_email(self, intent: ParsedIntent) -> str:
        """Handle send_email intent."""
        params = intent.params
        
        # Try to find the email to send
        entry = None
        
        # Check if we have a last draft
        if hasattr(self, '_last_draft'):
            entry = self._last_draft
        
        if not entry:
            return "❌ I don't know which email to send. Draft one first with: 'Draft an email for...'"
        
        # Confirm before sending
        response = f"""🚀 Ready to send to {entry.recipient_name or entry.company_name}!

**Subject:** {entry.subject}
**To:** {entry.recipient_email}

Type **'yes'** to confirm sending, or **'edit'** to modify."""
        
        # Store pending send
        self._pending_send = entry
        
        return response
    
    async def _handle_schedule_followup(self, intent: ParsedIntent) -> str:
        """Handle schedule_followup intent."""
        params = intent.params
        days = params.get("days_delay", 5)
        company = params.get("company_name", "this company")
        
        # In a real implementation, you'd look up the entry by company
        # For now, provide guidance
        return f"📅 I'll schedule a follow-up for {company} in {days} days.\n\n(Note: In the current implementation, use the Python API to schedule specific follow-ups)"
    
    async def _handle_check_replies(self, intent: ParsedIntent) -> str:
        """Handle check_replies intent."""
        company = intent.params.get("company_name")
        
        # Get daily stats
        stats = self.agent.memory.get_daily_stats()
        
        response = f"""📬 **Reply Check**

Today's activity:
• Emails sent: {stats.emails_sent}
• Replies received: {stats.replies_received}
• Positive responses: {stats.positive_responses}

"""
        
        if company:
            response += f"(Filtered for {company} - use Python API for detailed company-specific reply checking)"
        else:
            response += "Run `mubot-heartbeat` to check Gmail for new replies."
        
        return response
    
    async def _handle_add_opportunity(self, intent: ParsedIntent) -> str:
        """Handle add_opportunity intent."""
        from mubot.pipelines import JobPipeline
        
        params = intent.params
        company = params.get("company_name")
        role = params.get("role_title", "Software Engineer")
        
        if not company:
            return "❌ I need a company name. Try: 'Add Google to my pipeline'"
        
        pipeline = JobPipeline(self.agent.memory)
        opp = pipeline.add_opportunity(
            company_name=company,
            role_title=role,
            job_url=params.get("job_url"),
            notes=params.get("notes"),
        )
        
        return f"✅ Added **{company}** - {role} to your pipeline!\nID: {opp.id}\nStage: {opp.stage}"
    
    async def _handle_update_stage(self, intent: ParsedIntent) -> str:
        """Handle update_stage intent."""
        from mubot.pipelines import JobPipeline, PipelineStage
        
        params = intent.params
        company = params.get("company_name")
        new_stage = params.get("new_stage")
        
        if not company or not new_stage:
            return "❌ I need a company and stage. Try: 'Move Google to interview stage'"
        
        # Try to parse stage
        try:
            stage = PipelineStage(new_stage.lower())
        except ValueError:
            stages = ", ".join([s.value for s in PipelineStage])
            return f"❌ Unknown stage. Valid stages: {stages}"
        
        # Find opportunity by company name
        pipeline = JobPipeline(self.agent.memory)
        opps = [o for o in pipeline.get_active_opportunities() if o.company_name.lower() == company.lower()]
        
        if not opps:
            return f"❌ No active opportunity found for {company}. Add it first with 'Add {company} to my pipeline'"
        
        opp = pipeline.advance_stage(opps[0].id, stage)
        return f"✅ Updated **{company}** to **{stage.value}** stage!"
    
    async def _handle_get_summary(self, intent: ParsedIntent) -> str:
        """Handle get_summary intent."""
        params = intent.params
        period = params.get("period", "today")
        
        if period == "today":
            stats = self.agent.memory.get_daily_stats()
            return f"""📊 **Today's Summary**

• Emails sent: {stats.emails_sent}/{self.agent.settings.max_daily_emails}
• Replies received: {stats.replies_received}
• Positive: {stats.positive_responses}
• Rejections: {stats.rejections}

Daily limit: {'⚠️ Reached' if stats.limit_reached else '✅ OK'}
"""
        else:
            summary = await self.agent.get_daily_summary()
            return summary
    
    async def _handle_list_pipeline(self, intent: ParsedIntent) -> str:
        """Handle list_pipeline intent."""
        from mubot.pipelines import JobPipeline
        
        pipeline = JobPipeline(self.agent.memory)
        summary = pipeline.get_pipeline_summary()
        
        return summary
    
    async def _handle_pause_campaign(self, intent: ParsedIntent) -> str:
        """Handle pause_campaign intent."""
        reason = intent.params.get("reason", "User requested")
        self.agent.pause_campaign(reason)
        return f"⏸️  Campaign paused. Reason: {reason}\n\nNo emails will be sent until you resume."
    
    async def _handle_resume_campaign(self, intent: ParsedIntent) -> str:
        """Handle resume_campaign intent."""
        self.agent.resume_campaign()
        return "▶️  Campaign resumed! Emails can now be sent."
    
    async def _handle_company_info(self, intent: ParsedIntent) -> str:
        """Handle get_company_info intent."""
        company = intent.params.get("company_name")
        
        if not company:
            return "❌ Which company? Try: 'What do I know about Google?'"
        
        history = self.agent.get_company_context(company)
        
        return f"""🏢 **{company}** - Outreach History

• Total outreach: {history['total_outreach']}
• Responses received: {history['responses_received']}
• Last contact: {history['last_contact'] or 'Never'}
• Do not contact: {'⚠️ Yes' if history['do_not_contact'] else 'No'}

**What worked:**
{chr(10).join(['  • ' + w for w in history['what_worked']]) or '  No data yet'}
"""
    
    async def _handle_help(self, intent: ParsedIntent) -> str:
        """Handle help intent."""
        return """🤖 **MuBot - Natural Language Commands**

**Email Management:**
• "Draft a cold email for the senior engineer role at Stripe"
• "Draft an email to Sarah Chen at Meta about the PM role"
• "Send the email to Stripe"
• "Schedule a follow-up in 3 days"
• "Check if anyone replied"

**Pipeline Management:**
• "Add Google to my pipeline"
• "Add Meta - Software Engineer to my opportunities"
• "Move Stripe to interview stage"
• "What's in my pipeline?"
• "Show my daily summary"

**Campaign Control:**
• "Pause all emails"
• "Resume campaign"
• "What do I know about Google?"

**Tips:**
• Be specific about company names and roles
• You can reference "the email" after drafting one
• Always review emails before sending
"""
    
    async def _handle_unknown(self, intent: ParsedIntent) -> str:
        """Handle unknown intent."""
        return """🤔 I'm not sure what you'd like to do.

Try saying things like:
• "Draft a cold email for the engineer role at Google"
• "Add Stripe to my pipeline"
• "Show my daily summary"

Type **help** for more examples."""
    
    async def handle_confirmation(self, user_input: str) -> str:
        """
        Handle yes/no confirmation responses.
        
        Used after prompts like "Send this email? (yes/no)"
        """
        user_input = user_input.lower().strip()
        
        # Check for pending send
        if hasattr(self, '_pending_send') and self._pending_send:
            if user_input in ['yes', 'y', 'send', 'ok', 'sure']:
                entry = self._pending_send
                self._pending_send = None
                
                # Actually send
                success, msg = await self.agent.send_email(entry, approved=True)
                
                if success:
                    return f"✅ Email sent to {entry.recipient_name or entry.company_name}!"
                else:
                    return f"❌ Failed to send: {msg}"
            
            elif user_input in ['no', 'n', 'cancel', 'dont']:
                self._pending_send = None
                return "❌ Send cancelled. You can edit and try again."
            
            elif user_input in ['edit', 'change', 'modify']:
                return "✏️  Edit mode not yet implemented via chat. Use the Python API to modify drafts."
        
        return None  # Not a confirmation response

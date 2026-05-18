"""
MuBot Bot — Conversational agent with GPT-4 function calling.

Type natural language commands:
  list follow-ups
  cancel follow-ups for Netflix
  cancel Netflix follow-ups — I got rejected
  check replies
  what's working
  run campaign
  status
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from openai import AsyncOpenAI

from mubot.agent.core import JobSearchAgent
from mubot.config import get_settings


# OpenAI function calling format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_followups",
            "description": "List all scheduled follow-ups — shows pending, overdue, and already sent",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_followup",
            "description": (
                "Cancel all scheduled follow-ups for a specific company. "
                "Use reason='rejected' when the user was rejected through a non-email channel "
                "(LinkedIn, portal, call) — this also marks the row 'Rejected' in the Sheet. "
                "Omit reason for plain cancellation (e.g. user lost interest)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company name to cancel follow-ups for",
                    },
                    "reason": {
                        "type": "string",
                        "enum": ["rejected"],
                        "description": "Optional. 'rejected' also updates the Sheet status to 'Rejected'.",
                    },
                },
                "required": ["company"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_replies",
            "description": "Check Gmail for replies to sent outreach emails; auto-cancels follow-ups where replies were found",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_status",
            "description": "Show current job search status: emails sent today, pending follow-ups, overdue items",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_learnings",
            "description": "Show what email patterns are getting replies, response rate, and what isn't working",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_campaign",
            "description": "Run the email campaign from Google Sheets — draft and send initial emails to pending jobs",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max number of emails to send (default 10)"},
                    "dry_run": {"type": "boolean", "description": "Preview only, don't actually send"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_followups",
            "description": "Send all follow-up emails that are due now",
            "parameters": {
                "type": "object",
                "properties": {
                    "dry_run": {"type": "boolean", "description": "Preview only, don't send"},
                },
                "required": [],
            },
        },
    },
]


class MuBot:
    """
    Conversational job search bot.

    Uses GPT-4 function calling to route natural language to the right action.
    Run with: asyncio.run(MuBot().run())
    """

    def __init__(self):
        self.settings = get_settings()
        self.agent = JobSearchAgent()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.history: list[dict] = []

    async def initialize(self) -> bool:
        return await self.agent.initialize()

    def _system_prompt(self) -> str:
        state = self.agent.memory.load_heartbeat_state()
        unsent = [f for f in state.scheduled_followups if not f.get("sent")]
        return (
            f"You are MuBot, a job search assistant for {self.agent.user_profile.name}. "
            f"Today is {datetime.now().strftime('%Y-%m-%d')}. "
            f"Unsent follow-ups: {len(unsent)}. "
            "Call the appropriate tool for any action request. "
            "After tool results are shown, respond in 1-2 sentences max — the tool output is already visible."
        )

    async def _call_tool(self, name: str, args: dict) -> str:
        if name == "list_followups":
            return self._list_followups()
        if name == "cancel_followup":
            return await self._cancel_followup(args.get("company", ""), args.get("reason", ""))
        if name == "check_replies":
            return await self._check_replies()
        if name == "show_status":
            return self._show_status()
        if name == "show_learnings":
            return self._show_learnings()
        if name == "run_campaign":
            return await self._run_campaign(args.get("limit", 10), args.get("dry_run", False))
        if name == "run_followups":
            return await self._run_followups(args.get("dry_run", False))
        return f"Unknown tool: {name}"

    def _list_followups(self) -> str:
        state = self.agent.memory.load_heartbeat_state()
        all_fu = state.scheduled_followups
        if not all_fu:
            return "No follow-ups scheduled."

        now = datetime.now(timezone.utc)
        unsent = [f for f in all_fu if not f.get("sent")]
        sent_count = len(all_fu) - len(unsent)

        lines = [f"{len(unsent)} pending follow-ups:\n"]
        for f in sorted(unsent, key=lambda x: x.get("due_at", "")):
            company = f.get("company", "?")
            role = f.get("role", "")
            tag = f.get("followup_name", "")
            due_str = f.get("due_at", "")
            try:
                due = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                days = (due - now).days
                timing = f"in {days}d" if days > 0 else "OVERDUE"
            except Exception:
                timing = "?"
            lines.append(f"  • {company} — {tag} ({role}) [{timing}]")

        if sent_count:
            lines.append(f"\n  + {sent_count} already sent")
        return "\n".join(lines)

    async def _cancel_followup(self, company: str, reason: str = "") -> str:
        if not company:
            return "Specify a company name."
        target = company.strip().lower()
        state = self.agent.memory.load_heartbeat_state()
        matched = [
            f for f in state.scheduled_followups
            if f.get("company", "").strip().lower() == target
        ]
        state.scheduled_followups = [
            f for f in state.scheduled_followups
            if f.get("company", "").strip().lower() != target
        ]
        self.agent.memory.save_heartbeat_state(state)

        removed = len(matched)
        if not removed:
            return f"No follow-ups found matching '{company}'."

        msg = f"Cancelled {removed} follow-up(s) for '{company}'."

        if reason == "rejected":
            row_numbers = {f.get("row_number") for f in matched if f.get("row_number")}
            if not row_numbers:
                return msg + " (No sheet rows linked — Sheet status unchanged.)"
            try:
                from integrations.google_sheets import GoogleSheetsIntegration
                sheets = GoogleSheetsIntegration(
                    credentials_path="./credentials/sheets_credentials.json",
                    spreadsheet_name="Job Applications",
                )
                updated = 0
                for row in row_numbers:
                    if await sheets.update_job_status(row, "Rejected", datetime.now(timezone.utc)):
                        updated += 1
                msg += f" Marked {updated}/{len(row_numbers)} row(s) 'Rejected' in Sheet."
            except Exception as e:
                msg += f" (Sheet update failed: {e})"

        return msg

    async def _check_replies(self) -> str:
        from mubot.tools.gmail_client import GmailClient
        from mubot.scripts.run_heartbeat import check_inbox_for_replies

        settings = self.settings
        project_root = Path(__file__).parent.parent.parent.parent
        # Resolve credential paths from project root if they're relative
        creds = Path(settings.gmail_credentials_path)
        token = Path(settings.gmail_token_path)
        if not creds.is_absolute():
            settings.gmail_credentials_path = project_root / creds
        if not token.is_absolute():
            settings.gmail_token_path = project_root / token

        gmail = GmailClient(settings)
        authenticated = await gmail.authenticate()
        if not authenticated:
            return "Gmail authentication failed. Run `python reauth_gmail.py`."

        replies, cancelled = await check_inbox_for_replies(self.agent, gmail)
        return f"Found {replies} new replies, cancelled {cancelled} follow-ups."

    def _show_status(self) -> str:
        state = self.agent.memory.load_heartbeat_state()
        now = datetime.now(timezone.utc)
        unsent = [f for f in state.scheduled_followups if not f.get("sent")]

        overdue_count = 0
        for f in unsent:
            try:
                due = datetime.fromisoformat(f.get("due_at", "").replace("Z", "+00:00"))
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                if due <= now:
                    overdue_count += 1
            except Exception:
                pass

        lines = [
            f"Status — {datetime.now().strftime('%Y-%m-%d')}",
            f"  Emails sent today: {state.daily_email_count}",
            f"  Pending follow-ups: {len(unsent)} ({overdue_count} overdue)",
        ]
        if state.campaigns_paused:
            lines.append(f"  ⚠ Campaign PAUSED: {state.pause_reason}")
        if state.last_run:
            try:
                last = (
                    state.last_run.strftime("%Y-%m-%d %H:%M")
                    if hasattr(state.last_run, "strftime")
                    else str(state.last_run)[:16]
                )
                lines.append(f"  Last heartbeat: {last}")
            except Exception:
                pass
        return "\n".join(lines)

    def _show_learnings(self) -> str:
        from mubot.memory.learnings import LearningsTracker

        tracker = LearningsTracker(self.agent.memory.base_path)
        return tracker.get_summary()

    async def _run_campaign(self, limit: int = 10, dry_run: bool = False) -> str:
        from auto_campaign import AutomatedCampaign

        campaign = AutomatedCampaign(source="sheets", bulk=True)
        await campaign.initialize()
        await campaign.run_campaign(limit=limit, dry_run=dry_run)
        return "Campaign complete."

    async def _run_followups(self, dry_run: bool = False) -> str:
        from auto_campaign import AutomatedCampaign

        campaign = AutomatedCampaign(source="sheets", bulk=True)
        await campaign.initialize()
        await campaign.run_pending_followups(dry_run=dry_run)
        return "Follow-ups complete."

    async def chat(self, user_message: str) -> str:
        """Send a message, execute any tool calls, return final reply."""
        self.history.append({"role": "user", "content": user_message})

        messages = [{"role": "system", "content": self._system_prompt()}, *self.history]

        response = await self.client.chat.completions.create(
            model=self.settings.llm_model,
            max_tokens=1024,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            # Record assistant message with tool_calls attached
            self.history.append(msg)

            # Execute each tool and append tool result messages
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                result = await self._call_tool(tc.function.name, args)
                print(result)
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

            # Get brief follow-up
            final_messages = [{"role": "system", "content": self._system_prompt()}, *self.history]
            final = await self.client.chat.completions.create(
                model=self.settings.llm_model,
                max_tokens=256,
                messages=final_messages,
            )
            reply = final.choices[0].message.content or ""
        else:
            reply = msg.content or ""

        self.history.append({"role": "assistant", "content": reply})

        # Keep history bounded
        if len(self.history) > 20:
            self.history = self.history[-20:]

        return reply

    async def run(self):
        """Start the interactive bot loop."""
        print("=" * 60)
        print("🤖 MuBot — Your Job Search Bot")
        print("=" * 60)
        print()

        if not await self.initialize():
            print("❌ Failed to initialize. Run mubot-init first.")
            return

        first_name = self.agent.user_profile.name.split()[0]
        state = self.agent.memory.load_heartbeat_state()
        unsent = [f for f in state.scheduled_followups if not f.get("sent")]

        print(f"Hi {first_name}! {len(unsent)} follow-ups pending.")
        print()
        print("Commands: list follow-ups · cancel [company] (add 'rejected' if rejected) · check replies · what's working · run campaign · status")
        print("Type 'quit' to exit.")
        print()

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye", "q"):
                print("Bye!")
                break

            print()
            try:
                reply = await self.chat(user_input)
                if reply:
                    print(f"MuBot: {reply}")
            except Exception as e:
                print(f"❌ Error: {e}")
            print()

"""
MuBot CLI Commands

Consolidated command implementations for all CLI operations.
Replaces functionality from:
- mubot_cli.py (campaign, followups, list, cancel, sync, summary)
- mubot.py (_send_followups, _send_emails, _check_replies, etc.)
- mubot_daemon.py (_cmd_send_followups, _cmd_send_emails, etc.)
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Heartbeat path (consistent across all commands)
HEARTBEAT_PATH = Path("data/heartbeat-state.json")


class BaseCommands:
    """Base class for all command handlers."""
    
    def __init__(self, agent=None, sheets=None, verbose: bool = False):
        self.agent = agent
        self.sheets = sheets
        self.verbose = verbose
        
    def _load_heartbeat(self) -> dict:
        """Load heartbeat state."""
        if not HEARTBEAT_PATH.exists():
            return {"scheduled_followups": []}
        with open(HEARTBEAT_PATH) as f:
            return json.load(f)
    
    def _save_heartbeat(self, state: dict):
        """Save heartbeat state."""
        HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(HEARTBEAT_PATH, 'w') as f:
            json.dump(state, f, indent=2)


class CampaignCommands(BaseCommands):
    """Commands for running email campaigns."""
    
    async def run_campaign(self, limit: int = 50, dry_run: bool = False, bulk: bool = False):
        """Run email campaign from Google Sheets."""
        from auto_campaign import AutomatedCampaign
        
        campaign = AutomatedCampaign(source="sheets", bulk=bulk)
        await campaign.initialize()
        await campaign.run_campaign(limit=limit, dry_run=dry_run)
    
    async def send_emails(self, limit: int = 10, dry_run: bool = False, bulk: bool = False):
        """Send initial emails from sheet."""
        print("📋 Checking Google Sheet for pending jobs...")
        
        from integrations.google_sheets import GoogleSheetsIntegration
        from auto_campaign import AutomatedCampaign
        
        sheets = GoogleSheetsIntegration(
            credentials_path="./credentials/sheets_credentials.json",
            spreadsheet_name="Job Applications"
        )
        
        pending = await sheets.get_pending_jobs(limit=limit)
        
        if not pending:
            return {"success": True, "message": "✅ No pending jobs in your sheet"}
        
        print(f"🎯 Sending {len(pending)} initial emails...")
        
        campaign = AutomatedCampaign(source="sheets", bulk=bulk)
        await campaign.initialize()
        
        sent = 0
        errors = []
        for i, job in enumerate(pending, 1):
            company = job.get('company', 'Unknown')
            print(f"  [{i}/{len(pending)}] {company} → {job.get('email')}", end=" ")
            
            try:
                await campaign._process_job(job, dry_run=dry_run)
                sent += 1
                print("✅")
            except Exception as e:
                print(f"❌ ({e})")
                errors.append(f"{company}: {e}")
        
        message = f"✅ Sent {sent}/{len(pending)} emails"
        if errors:
            message += f"\n⚠️  {len(errors)} errors"
        
        return {"success": sent > 0, "message": message, "sent": sent, "total": len(pending), "errors": errors}


class FollowupCommands(BaseCommands):
    """Commands for follow-up management."""
    
    async def send_followups(self, dry_run: bool = False, bulk: bool = False, limit: Optional[int] = None):
        """Send pending follow-ups."""
        from auto_campaign import AutomatedCampaign
        
        campaign = AutomatedCampaign(source="sheets", bulk=bulk)
        await campaign.initialize()
        await campaign.run_pending_followups(dry_run=dry_run, limit=limit)
    
    def list_followups(self, show_all: bool = False):
        """List all pending follow-ups."""
        state = self._load_heartbeat()
        followups = state.get("scheduled_followups", [])
        
        unsent = [f for f in followups if not f.get("sent", False)]
        sent = [f for f in followups if f.get("sent", False)]
        
        print(f"\n📊 Follow-up Summary:")
        print(f"   Total: {len(followups)}")
        print(f"   ✅ Sent: {len(sent)}")
        print(f"   ⏳ Pending: {len(unsent)}")
        
        if unsent:
            print(f"\n📅 Pending Follow-ups:")
            print("-" * 80)
            
            # Group by company
            by_company = {}
            for f in unsent:
                company = f.get("company", "Unknown")
                if company not in by_company:
                    by_company[company] = []
                by_company[company].append(f)
            
            now = datetime.now(timezone.utc)
            
            for company, items in sorted(by_company.items()):
                print(f"\n🏢 {company}:")
                for f in items:
                    due = f.get("due_at", "Unknown")[:10]
                    name = f.get("followup_name", "N/A")
                    email = f.get("email", "No email")
                    
                    # Check if overdue
                    try:
                        due_str = f.get("due_at", "")
                        if due_str.endswith('Z'):
                            due_dt = datetime.fromisoformat(due_str.replace('Z', '+00:00'))
                        elif '+' in due_str or '-' in due_str[-6:]:
                            due_dt = datetime.fromisoformat(due_str)
                        else:
                            due_dt = datetime.fromisoformat(due_str).replace(tzinfo=timezone.utc)
                        overdue = "⚠️ OVERDUE" if due_dt < now else ""
                    except:
                        overdue = ""
                    
                    print(f"   • {name} → {email} (Due: {due}) {overdue}")
        
        if show_all and sent:
            print(f"\n📬 Sent Follow-ups:")
            print("-" * 80)
            by_company = {}
            for f in sent:
                company = f.get("company", "Unknown")
                if company not in by_company:
                    by_company[company] = []
                by_company[company].append(f)
            
            for company, items in sorted(by_company.items()):
                print(f"\n🏢 {company}:")
                for f in items:
                    sent_at = f.get("sent_at", "Unknown")
                    if sent_at and len(str(sent_at)) > 10:
                        sent_at = str(sent_at)[:10]
                    name = f.get("followup_name", "N/A")
                    print(f"   ✅ {name} (Sent: {sent_at})")
    
    def cancel_followups(self, company_name: str, force: bool = False):
        """Cancel follow-ups for a company."""
        state = self._load_heartbeat()
        followups = state.get("scheduled_followups", [])
        
        to_cancel = [f for f in followups if company_name.lower() in f.get("company", "").lower()]
        remaining = [f for f in followups if company_name.lower() not in f.get("company", "").lower()]
        
        if not to_cancel:
            print(f"❌ No follow-ups found for '{company_name}'")
            return
        
        print(f"\n🗑️  Found {len(to_cancel)} follow-up(s) for '{company_name}':")
        for f in to_cancel:
            print(f"   • {f.get('followup_name')} → {f.get('email')}")
        
        if not force:
            confirm = input(f"\nCancel these {len(to_cancel)} follow-up(s)? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("❌ Cancelled")
                return
        
        state["scheduled_followups"] = remaining
        self._save_heartbeat(state)
        print(f"✅ Cancelled {len(to_cancel)} follow-up(s)")
    
    def mark_sent(self, company_name: str):
        """Mark follow-ups as sent without actually sending."""
        state = self._load_heartbeat()
        followups = state.get("scheduled_followups", [])
        
        marked = 0
        for f in followups:
            if company_name.lower() in f.get("company", "").lower():
                if not f.get("sent", False):
                    f["sent"] = True
                    f["sent_at"] = datetime.now(timezone.utc).isoformat()
                    marked += 1
                    print(f"   ✅ Marked {f.get('followup_name')} as sent")
        
        if marked > 0:
            self._save_heartbeat(state)
            print(f"\n✅ Marked {marked} follow-up(s) as sent")
        else:
            print(f"❌ No pending follow-ups found for '{company_name}'")
    
    def reschedule(self, company_name: str, days: int):
        """Reschedule follow-ups."""
        state = self._load_heartbeat()
        followups = state.get("scheduled_followups", [])
        
        rescheduled = 0
        new_due = datetime.now(timezone.utc) + timedelta(days=days)
        
        for f in followups:
            if company_name.lower() in f.get("company", "").lower():
                if not f.get("sent", False):
                    f["due_at"] = new_due.isoformat()
                    rescheduled += 1
                    print(f"   📅 Rescheduled {f.get('followup_name')} to {new_due.strftime('%Y-%m-%d')}")
        
        if rescheduled > 0:
            self._save_heartbeat(state)
            print(f"\n✅ Rescheduled {rescheduled} follow-up(s) to {days} days from now")
        else:
            print(f"❌ No pending follow-ups found for '{company_name}'")


class StatusCommands(BaseCommands):
    """Commands for status and reporting."""
    
    async def show_status(self) -> dict:
        """Show current status."""
        print("📊 Getting status...")
        
        state = self._load_heartbeat()
        now = datetime.now(timezone.utc)
        
        # Count stats
        all_followups = state.get("scheduled_followups", [])
        sent = [f for f in all_followups if f.get('sent')]
        pending = [f for f in all_followups if not f.get('sent')]
        
        # Count overdue
        overdue = []
        for f in pending:
            due_at_str = f.get('due_at', '9999-01-01')
            try:
                if due_at_str.endswith('Z'):
                    due_at = datetime.fromisoformat(due_at_str.replace('Z', '+00:00'))
                elif '+' in due_at_str or '-' in due_at_str[-6:]:
                    due_at = datetime.fromisoformat(due_at_str)
                else:
                    due_at = datetime.fromisoformat(due_at_str).replace(tzinfo=timezone.utc)
                if due_at < now:
                    overdue.append(f)
            except (ValueError, TypeError):
                continue
        
        # Group pending by company
        by_company = {}
        for f in pending:
            c = f.get('company', 'Unknown')
            if c not in by_company:
                by_company[c] = []
            by_company[c].append(f)
        
        message = f"""📊 MuBot Status

   📧 Total follow-ups: {len(all_followups)}
   ✅ Sent: {len(sent)}
   ⏳ Pending: {len(pending)}
   ⚠️  Overdue: {len(overdue)}
"""
        
        if overdue:
            message += f"\n   🏢 Companies needing follow-ups:\n"
            for company in list(by_company.keys())[:10]:
                count = len(by_company[company])
                message += f"      • {company}: {count} pending\n"
            
            if len(by_company) > 10:
                message += f"      ... and {len(by_company) - 10} more\n"
            
            message += f"\n   💡 Run 'python mubot.py \"send my follow-ups\"' to send them"
        
        return {"success": True, "message": message}
    
    async def show_summary(self):
        """Show activity summary."""
        print("=" * 70)
        print("📊 MuBot Activity Summary")
        print("=" * 70)
        
        # Follow-up stats
        state = self._load_heartbeat()
        followups = state.get("scheduled_followups", [])
        unsent = [f for f in followups if not f.get("sent", False)]
        sent = [f for f in followups if f.get("sent", False)]
        
        print(f"\n📧 Follow-ups:")
        print(f"   Total: {len(followups)}")
        print(f"   Sent: {len(sent)}")
        print(f"   Pending: {len(unsent)}")
        
        # Count overdue
        now = datetime.now(timezone.utc)
        overdue = []
        for f in unsent:
            due_at_str = f.get("due_at", "9999-01-01")
            try:
                if due_at_str.endswith('Z'):
                    due_at = datetime.fromisoformat(due_at_str.replace('Z', '+00:00'))
                elif '+' in due_at_str or '-' in due_at_str[-6:]:
                    due_at = datetime.fromisoformat(due_at_str)
                else:
                    due_at = datetime.fromisoformat(due_at_str).replace(tzinfo=timezone.utc)
                if due_at < now:
                    overdue.append(f)
            except (ValueError, TypeError):
                continue
        
        if overdue:
            print(f"   ⚠️  Overdue: {len(overdue)}")
        
        # Google Sheets stats
        try:
            from integrations.google_sheets import GoogleSheetsIntegration
            sheets = GoogleSheetsIntegration(
                credentials_path="./credentials/sheets_credentials.json",
                spreadsheet_name="Job Applications"
            )
            
            raw_records = sheets.sheet.get_all_records()
            records = [{k.strip(): v for k, v in r.items()} for r in raw_records]
            
            status_counts = {}
            for r in records:
                status = str(r.get("Status", "Unknown")).strip() or "Pending"
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"\n📋 Google Sheets Status:")
            for status, count in sorted(status_counts.items()):
                print(f"   {status}: {count}")
            
            print(f"\n   Sheet URL: {sheets.get_sheet_url()}")
        except Exception as e:
            print(f"\n⚠️  Could not load sheet stats: {e}")
    
    async def check_replies(self):
        """Check Gmail for replies."""
        print("📬 Checking Gmail for replies...")
        
        from mubot.agent import JobSearchAgent
        from mubot.tools.gmail_client import GmailClient
        
        agent = JobSearchAgent()
        await agent.initialize()
        
        gmail = GmailClient(agent.settings)
        await gmail.authenticate()
        
        # Search for recent emails with outreach labels
        messages = await gmail.search_messages("label:outreach/sent newer_than:7d", max_results=50)
        
        replies_found = 0
        companies_with_replies = []
        
        for msg in messages:
            thread_id = msg.get('threadId')
            if thread_id:
                replies = await gmail.check_for_replies(msg.get('id'), thread_id)
                if replies:
                    replies_found += len(replies)
                    subject = msg.get('subject', '')
                    companies_with_replies.append(subject)
        
        if replies_found:
            message = f"📬 Found {replies_found} new replies!\n\n"
            message += "Companies that replied:\n"
            for c in companies_with_replies[:5]:
                message += f"  • {c[:50]}...\n"
        else:
            message = "📭 No new replies yet. Keep following up!"
        
        print(message)
        return {"success": True, "message": message, "replies": replies_found}


class SyncCommands(BaseCommands):
    """Commands for syncing data."""
    
    async def sync_sheets(self, dry_run: bool = False):
        """Sync follow-up status to Google Sheets."""
        print("🔄 Syncing follow-up status to Google Sheets...")
        
        from integrations.google_sheets import GoogleSheetsIntegration
        
        sheets = GoogleSheetsIntegration(
            credentials_path="./credentials/sheets_credentials.json",
            spreadsheet_name="Job Applications"
        )
        
        result = await sheets.sync_followups_to_sheet(dry_run=dry_run)
        
        updated = result.get('updated', 0)
        message = f"✅ Synced {updated} rows to Google Sheets"
        print(message)
        return {"success": True, "message": message, "updated": updated}

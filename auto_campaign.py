#!/usr/bin/env python3
"""
Automated Email Campaign Runner

Reads jobs from Google Sheets or Notion, drafts/sends emails,
and schedules follow-ups automatically.

Usage:
    # Run manually
    python auto_campaign.py --source sheets --limit 5
    
    # Schedule with cron (daily at 9 AM)
    0 9 * * * cd /path/to/mubot && python auto_campaign.py --source sheets

Follow-up Schedule:
    - Follow-up 1: After 4 working days
    - Follow-up 2: After 8 working days
    - Follow-up 3: After 10 working days
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mubot.agent import JobSearchAgent
from integrations.google_sheets import GoogleSheetsIntegration, add_working_days
from integrations.notion_integration import NotionIntegration


class AutomatedCampaign:
    """
    Automated job search email campaign.
    
    Connects to a data source (Sheets/Notion), processes pending jobs,
    sends emails, and schedules follow-ups.
    """
    
    def __init__(self, source: str = "sheets", bulk: bool = False):
        self.source = source
        self.bulk = bulk
        self.agent = JobSearchAgent()
        self.integration = None
        
    async def initialize(self):
        """Initialize agent and integration."""
        print("🚀 Initializing MuBot...")
        await self.agent.initialize()
        
        # Initialize integration
        if self.source == "sheets":
            self.integration = GoogleSheetsIntegration(
                credentials_path="./credentials/sheets_credentials.json",
                spreadsheet_name="Job Applications"
            )
        elif self.source == "notion":
            from mubot.config import get_settings
            settings = get_settings()
            
            self.integration = NotionIntegration(
                token=settings.notion_api_token or "secret_xxx",
                database_id=settings.notion_database_id or "xxx-xxx-xxx"
            )
        else:
            raise ValueError(f"Unknown source: {self.source}")
        
        print(f"✅ Connected to {self.source}")
    
    async def run_campaign(self, limit: int = 10, dry_run: bool = False):
        """
        Run the automated campaign.
        
        Args:
            limit: Maximum number of jobs to process
            dry_run: If True, don't actually send emails (preview mode)
        """
        print(f"\n{'='*60}")
        print(f"📧 Automated Campaign ({self.source.upper()})")
        print(f"{'='*60}\n")
        
        if dry_run:
            print("🏃 DRY RUN MODE - No emails will be sent\n")
        
        # Get pending jobs
        print("🔍 Fetching pending jobs...")
        pending_jobs = await self.integration.get_pending_jobs(limit=limit)
        
        if not pending_jobs:
            print("✅ No pending jobs found. You're all caught up!")
            return
        
        print(f"📋 Found {len(pending_jobs)} pending jobs\n")
        
        # Process each job
        for i, job in enumerate(pending_jobs, 1):
            print(f"\n{'─'*60}")
            print(f"📧 Job {i}/{len(pending_jobs)}: {job['company']} - {job['role']}")
            print(f"{'─'*60}")
            
            await self._process_job(job, dry_run)
            
            # Small delay between jobs
            if i < len(pending_jobs):
                await asyncio.sleep(2)
        
        print(f"\n{'='*60}")
        print("✅ Campaign Complete!")
        print(f"{'='*60}")
    
    async def _process_job(self, job: dict, dry_run: bool = False):
        """Process a single job."""
        company = job['company']
        role = job['role']
        recipient = job['recipient_name'] or "Hiring Manager"
        email = job['email']
        jd = job['job_description']
        
        # Validate required fields
        if not company or not role:
            print("❌ Missing company or role. Skipping.")
            return
        
        if not email:
            print("⚠️  No email provided. Will draft only.")
        
        # Draft email
        print(f"📝 Drafting email for {role} at {company}...")
        
        try:
            if jd and len(jd) > 50:
                # Use JD-enhanced version
                draft = await self.agent.reasoning.draft_email_with_jd(
                    user_profile=self.agent.user_profile,
                    company_name=company,
                    role_title=role,
                    company_context=f"{company} - innovative company",
                    job_description=jd,
                    recipient_name=recipient
                )
                print("   ✓ JD-enhanced draft created")
            else:
                # Use regular version
                draft, warnings = await self.agent.draft_email(
                    company_name=company,
                    role_title=role,
                    company_context=f"{company} - innovative company",
                    recipient_name=recipient,
                    recipient_email=email
                )
                if warnings:
                    print(f"   ⚠️  Warnings: {warnings}")
                print("   ✓ Standard draft created")
            
            # Show draft preview
            print(f"\n   Subject: {draft.subject}")
            print(f"   Body preview: {draft.body[:150]}...\n")
            
            if dry_run:
                print("   🏃 DRY RUN - Would send email and schedule follow-ups")
                return
            
            # Confirm before sending (unless in bulk mode)
            if email:
                if self.bulk:
                    # Bulk mode: auto-send without confirmation
                    print(f"   🚀 BULK MODE: Auto-sending to {email}")
                    confirm = "yes"
                else:
                    confirm = input(f"   Send to {email}? (yes/no/skip): ").strip().lower()
                
                if confirm == "skip":
                    print("   ⏭️  Skipping this job")
                    return
                
                if confirm == "yes":
                    # Send email with resume attachment if available
                    draft.recipient_email = email
                    
                    # Get resume path from user profile
                    resume_attachments = None
                    if self.agent.user_profile and self.agent.user_profile.resume_path:
                        resume_attachments = [str(self.agent.user_profile.resume_path)]
                        print(f"   📎 Attaching: {self.agent.user_profile.resume_path.name}")
                    
                    success, msg = await self.agent.send_email(
                        draft, approved=True, attachments=resume_attachments
                    )
                    
                    if success:
                        print(f"   ✅ {msg}")
                        
                        # Schedule follow-ups
                        await self._schedule_followups(draft, job)
                        
                        # Update status in source
                        await self._update_job_status(job, "Sent")
                        
                        # Bulk mode: add delay before next email
                        if self.bulk:
                            print("   ⏱️  Waiting 5 seconds before next email...")
                            import asyncio
                            await asyncio.sleep(5)
                    else:
                        print(f"   ❌ Failed: {msg}")
                        await self._update_job_status(job, "Send Failed")
                else:
                    print("   ❌ Send cancelled")
                    await self._update_job_status(job, "Drafted - Not Sent")
            else:
                # No email, just save draft
                print("   💾 Draft saved (no email to send)")
                await self._update_job_status(job, "Drafted")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            await self._update_job_status(job, f"Error: {str(e)[:50]}")
    
    async def _schedule_followups(self, draft, job: dict):
        """Schedule the 3 follow-ups with JD and thread_id."""
        print("\n   📅 Scheduling follow-ups...")
        
        now = datetime.utcnow()
        
        # Calculate working days
        followup_1 = add_working_days(now, 4)   # 4 working days
        followup_2 = add_working_days(now, 8)   # 8 working days
        followup_3 = add_working_days(now, 10)  # 10 working days
        
        followups = [
            (followup_1, "Follow-up 1"),
            (followup_2, "Follow-up 2"),
            (followup_3, "Follow-up 3"),
        ]
        
        for date, name in followups:
            days_until = (date - now).days
            print(f"      • {name}: {date.strftime('%Y-%m-%d')} ({days_until} days)")
        
        # Store in heartbeat state
        state = self.agent.memory.load_heartbeat_state()
        
        # Get job description from job
        job_description = job.get('job_description', '') or job.get('Job Description', '')
        
        for date, name in followups:
            state.scheduled_followups.append({
                "entry_id": draft.id,
                "company": job['company'],
                "role": job['role'],
                "email": draft.recipient_email,
                "recipient_name": draft.recipient_name or "Hiring Manager",
                "job_description": job_description,
                "thread_id": draft.gmail_thread_id,  # For replying in same thread
                "due_at": date.isoformat(),
                "followup_name": name,
                "sent": False
            })
        
        self.agent.memory.save_heartbeat_state(state)
        print("   ✅ 3 follow-ups scheduled")
    
    async def _update_job_status(self, job: dict, status: str):
        """Update job status in the source."""
        try:
            if self.source == "sheets":
                await self.integration.update_job_status(
                    job.get('row_number', 0),
                    status,
                    datetime.utcnow()
                )
            elif self.source == "notion":
                await self.integration.update_job_status(
                    job.get('page_id', ''),
                    status,
                    datetime.utcnow()
                )
        except Exception as e:
            print(f"   ⚠️  Could not update status: {e}")
    
    async def run_pending_followups(self, dry_run: bool = False):
        """Check and send any due follow-ups."""
        print(f"\n{'='*60}")
        print("📅 Checking Pending Follow-ups")
        print(f"{'='*60}\n")
        
        state = self.agent.memory.load_heartbeat_state()
        now = datetime.utcnow()
        
        due_followups = []
        for task in state.scheduled_followups:
            if task.get('sent'):
                continue
            
            due_at = datetime.fromisoformat(task.get('due_at', '').replace('Z', '+00:00'))
            if due_at <= now:
                due_followups.append(task)
        
        if not due_followups:
            print("✅ No follow-ups due today")
            return
        
        print(f"📧 {len(due_followups)} follow-ups due:\n")
        
        for task in due_followups:
            company = task.get('company', 'Unknown')
            email = task.get('email', '')
            name = task.get('followup_name', 'Follow-up')
            
            print(f"   {name} for {company} ({email})")
            
            if dry_run:
                print("      🏃 DRY RUN - Would send\n")
                continue
            
            confirm = input("      Send now? (yes/no): ").strip().lower()
            
            if confirm == "yes" and email:
                # Draft and send follow-up
                success = await self._send_followup_email(task, name)
                if success:
                    task['sent'] = True
            else:
                print(f"      ❌ Skipped\n")
        
        # Save updated state
        self.agent.memory.save_heartbeat_state(state)
    
    async def _send_followup_email(self, task: dict, followup_name: str) -> bool:
        """Draft and send a follow-up email."""
        try:
            from mubot.memory.models import OutreachEntry, OutreachStatus
            
            company = task.get('company', 'Unknown')
            role = task.get('role', 'Role')
            email = task.get('email', '')
            
            # Determine follow-up number and tone
            if '1' in followup_name:
                followup_num = 1
                tone = "gentle reminder"
            elif '2' in followup_name:
                followup_num = 2
                tone = "adding value"
            else:
                followup_num = 3
                tone = "final follow-up"
            
            # Get names for personalization
            recipient_name = task.get('recipient_name', 'Hiring Manager')
            sender_name = self.agent.user_profile.name if self.agent.user_profile else 'Muskan'
            
            # Create a minimal entry for follow-up generation
            original_entry = OutreachEntry(
                id=task.get('entry_id', 'unknown'),
                company_name=company,
                role_title=role,
                recipient_email=email,
                recipient_name=recipient_name,
                subject=f"Re: {role} at {company}",
                body="",
                status=OutreachStatus.SENT,
                followup_count=followup_num - 1,
            )
            
            # Get job description for context
            job_description = task.get('job_description', '')
            
            # Draft follow-up (with JD context)
            print(f"      📝 Drafting {followup_name}...")
            
            followup_response = await self.agent.reasoning.draft_followup(
                original_entry=original_entry,
                days_elapsed=4 if followup_num == 1 else (8 if followup_num == 2 else 10),
                job_description=job_description
            )
            
            # Parse subject and body from response
            followup_lines = followup_response.split('\n')
            followup_subject = f"Re: {role}"
            followup_body = followup_response
            
            # Extract subject if present
            for i, line in enumerate(followup_lines):
                if line.lower().startswith('subject:'):
                    followup_subject = line.split(':', 1)[1].strip()
                    followup_body = '\n'.join(followup_lines[i+1:]).strip()
                    break
            
            # Replace placeholders with actual names
            followup_body = followup_body.replace('[Recipient\'s Name]', recipient_name)
            followup_body = followup_body.replace('[Hiring Manager\'s Name]', recipient_name)
            followup_body = followup_body.replace('[Name]', recipient_name)
            followup_body = followup_body.replace('[Your Name]', sender_name.split()[0])  # First name
            
            # Build contact info line
            contact_info = sender_name
            if self.agent.user_profile:
                if self.agent.user_profile.phone:
                    contact_info += f" | {self.agent.user_profile.phone}"
                if self.agent.user_profile.linkedin_url:
                    contact_info += f" | {self.agent.user_profile.linkedin_url}"
            
            followup_body = followup_body.replace('[Your Contact Information]', contact_info)
            
            # Show preview
            print(f"      Subject: {followup_subject}")
            print(f"      Body: {followup_body[:100]}...")
            
            # Confirm send
            confirm = input(f"      Send this {followup_name}? (yes/no): ").strip().lower()
            
            if confirm == "yes":
                # Send via Gmail (in same thread as original)
                from mubot.tools.gmail_client import GmailClient
                gmail = GmailClient(self.agent.settings)
                authenticated = await gmail.authenticate()
                
                if not authenticated:
                    print("      ❌ Gmail authentication failed")
                    return False
                
                # Get thread_id for replying in same thread
                thread_id = task.get('thread_id')
                
                result = await gmail.send_email(
                    to=email,
                    subject=followup_subject,
                    body=followup_body.replace('\n', '<br>'),
                    thread_id=thread_id,  # Reply in same thread
                    apply_label=True
                )
                
                if result and result.get('message_id'):
                    print(f"      ✅ {followup_name} sent successfully!")
                    if thread_id:
                        print(f"      📎 Replied in thread: {thread_id[:20]}...")
                    return True
                else:
                    print(f"      ❌ Failed to send")
                    return False
            else:
                print(f"      ❌ Cancelled")
                return False
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated MuBot Email Campaign"
    )
    parser.add_argument(
        "--source",
        choices=["sheets", "notion"],
        default="sheets",
        help="Data source (default: sheets)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum jobs to process (default: 10)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mode - don't send emails"
    )
    parser.add_argument(
        "--followups-only",
        action="store_true",
        help="Only run pending follow-ups"
    )
    parser.add_argument(
        "--bulk",
        action="store_true",
        help="Bulk mode - send emails without confirmation prompts"
    )
    
    args = parser.parse_args()
    
    async def run():
        campaign = AutomatedCampaign(source=args.source, bulk=args.bulk)
        await campaign.initialize()
        
        if args.followups_only:
            await campaign.run_pending_followups(dry_run=args.dry_run)
        else:
            await campaign.run_campaign(limit=args.limit, dry_run=args.dry_run)
            await campaign.run_pending_followups(dry_run=args.dry_run)
    
    asyncio.run(run())


if __name__ == "__main__":
    main()

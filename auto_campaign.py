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
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mubot.agent import JobSearchAgent
from integrations.google_sheets import GoogleSheetsIntegration


def add_working_days(start_date: datetime, working_days: int) -> datetime:
    """Add working days (excluding weekends) to a date."""
    current = start_date
    days_added = 0
    
    while days_added < working_days:
        current += timedelta(days=1)
        # Skip weekends (5=Saturday, 6=Sunday)
        if current.weekday() < 5:
            days_added += 1
    
    return current


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
            
            from integrations.notion_integration import NotionIntegration
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
    
    @staticmethod
    def _parse_role(raw_role: str) -> tuple[str, str]:
        """
        Split 'Data Scientist II R2619158' into ('Data Scientist II', 'R2619158').
        Returns (clean_role, job_id) where job_id is '' if none found.
        """
        match = re.search(r'\b([A-Z]{0,3}\d{5,10})\b', raw_role)
        if match:
            job_id = match.group(1)
            clean = raw_role[:match.start()].strip().rstrip('-').strip()
            return clean, job_id
        return raw_role.strip(), ""

    async def _process_job(self, job: dict, dry_run: bool = False):
        """Process a single job."""
        company = job['company']
        raw_role = job['role']
        role, job_id = self._parse_role(raw_role)
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

        # Select role-specific skills
        role_skills = self.agent._select_skills_for_role(role)

        try:
            if jd and len(jd) > 50:
                # Use JD-enhanced version
                draft = await self.agent.reasoning.draft_email_with_jd(
                    user_profile=self.agent.user_profile,
                    company_name=company,
                    role_title=role,
                    job_reference=job_id,
                    company_context=f"{company} - innovative company",
                    job_description=jd,
                    recipient_name=recipient,
                    role_skills=role_skills,
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
            
            # In bulk mode, send without confirmation
            if self.bulk and email:
                # Add 5-second delay before sending
                print("   ⏱️  Waiting 5 seconds before sending...")
                await asyncio.sleep(5)

                draft.recipient_email = email
                per_job_resume = job.get("resume", "")
                extra_attachments = [per_job_resume] if per_job_resume else None
                if per_job_resume:
                    print(f"   📎 Using custom resume: {per_job_resume}")
                success, msg = await self.agent.send_email(draft, approved=True, attachments=extra_attachments)
                
                if success:
                    print(f"   ✅ {msg}")
                    
                    # Schedule follow-ups
                    await self._schedule_followups(draft, job)
                    
                    # Update status in source
                    await self._update_job_status(job, "Sent")
                else:
                    print(f"   ❌ Failed: {msg}")
                    await self._update_job_status(job, "Send Failed")
                return
            
            # Confirm before sending (interactive mode)
            if email:
                confirm = input(f"   Send to {email}? (yes/no/skip): ").strip().lower()
                
                if confirm == "skip":
                    print("   ⏭️  Skipping this job")
                    return
                
                if confirm == "yes":
                    # Send email
                    draft.recipient_email = email
                    success, msg = await self.agent.send_email(draft, approved=True)
                    
                    if success:
                        print(f"   ✅ {msg}")
                        
                        # Schedule follow-ups
                        await self._schedule_followups(draft, job)
                        
                        # Update status in source
                        await self._update_job_status(job, "Sent")
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
        """Schedule the 3 follow-ups."""
        print("\n   📅 Scheduling follow-ups...")
        
        now = datetime.now(timezone.utc)
        
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
        
        for date, name in followups:
            state.scheduled_followups.append({
                "entry_id": draft.id,
                "company": job['company'],
                "role": job['role'],
                "email": draft.recipient_email,
                "recipient_name": draft.recipient_name or job.get('recipient_name') or "Hiring Manager",
                "thread_id": draft.gmail_thread_id,  # Store thread_id for replies
                "job_description": job.get('job_description', ''),  # Store JD for follow-up context
                "due_at": date.isoformat(),
                "followup_name": name,
                "sent": False,
                "row_number": job.get('row_number'),  # Store for sheet updates
                "job_description": job.get('job_description', '')[:300]  # Brief context only
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
                    datetime.now(timezone.utc)
                )
            elif self.source == "notion":
                await self.integration.update_job_status(
                    job.get('page_id', ''),
                    status,
                    datetime.now(timezone.utc)
                )
        except Exception as e:
            print(f"   ⚠️  Could not update status: {e}")
    
    async def _update_followup_status(self, task: dict, followup_name: str):
        """Update Google Sheet status after sending a follow-up."""
        row_number = task.get('row_number')
        if not row_number:
            print(f"   ⚠️  Cannot update sheet: row_number not found in task")
            return
        
        # Determine status based on follow-up number
        if '1' in followup_name:
            status = "FU1 Sent"
            fu_count = 1
        elif '2' in followup_name:
            status = "FU2 Sent"
            fu_count = 2
        elif '3' in followup_name:
            status = "FU3 Sent"
            fu_count = 3
        else:
            status = "Follow-up Sent"
            fu_count = 1
        
        try:
            if self.source == "sheets":
                # Update status column
                await self.integration.update_job_status(
                    row_number,
                    status,
                    datetime.now(timezone.utc)
                )
                # Update follow-up count column
                await self.integration.update_followup_count(row_number, fu_count)
                print(f"   ✅ Sheet updated: {status}")
            elif self.source == "notion":
                # Notion update logic if needed
                pass
        except Exception as e:
            print(f"   ⚠️  Could not update sheet: {e}")
    
    async def check_for_replies(self):
        """Check Gmail for replies and auto-cancel follow-ups."""
        from mubot.tools.gmail_client import GmailClient
        from mubot.memory.models import OutreachEntry, OutreachStatus
        
        # Check if we have any follow-ups to check
        state = self.agent.memory.load_heartbeat_state()
        unsent_followups = [f for f in state.scheduled_followups if not f.get('sent', False)]
        
        if not unsent_followups:
            print("✅ No pending follow-ups to check")
            return
        
        print(f"📬 Checking {len(unsent_followups)} unsent follow-ups for replies...")
        
        # Authenticate Gmail
        gmail = GmailClient(self.agent.settings)
        authenticated = await gmail.authenticate()
        
        if not authenticated:
            print("❌ Gmail authentication failed")
            return
        
        replies_found = 0
        followups_cancelled = 0
        processed_threads = set()
        
        # Check follow-ups with thread_ids
        followups_with_threads = [f for f in unsent_followups if f.get('thread_id')]
        print(f"   Checking {len(followups_with_threads)} threads...")
        
        for followup in followups_with_threads:
            thread_id = followup.get('thread_id')
            company = followup.get('company', 'Unknown')
            
            if thread_id in processed_threads:
                continue
            processed_threads.add(thread_id)
            
            try:
                # Get messages in thread
                messages = await gmail.get_replies(thread_id)
                
                if len(messages) > 1:
                    # Filter to only incoming messages
                    sender_email = self.agent.user_profile.email if self.agent.user_profile else ""
                    incoming = [
                        m for m in messages 
                        if sender_email not in m.get('from', '')
                    ]
                    
                    if incoming:
                        reply = incoming[-1]
                        replies_found += 1
                        
                        print(f"\n   📨 Reply from {company}!")
                        print(f"      From: {reply.get('from', 'Unknown')}")
                        print(f"      Subject: {reply.get('subject', 'No subject')}")
                        preview = reply.get('body', '')[:100].replace('\n', ' ')
                        print(f"      Preview: {preview}...")
                        
                        # Create entry and process response
                        entry = OutreachEntry(
                            id=followup.get('entry_id', f"temp-{thread_id}"),
                            company_name=company,
                            role_title=followup.get('role', 'Role'),
                            recipient_email=followup.get('email', ''),
                            recipient_name=followup.get('recipient_name', 'Hiring Manager'),
                            subject=reply.get('subject', f"Re: {followup.get('role', 'Role')}"),
                            body="",
                            status=OutreachStatus.SENT,
                            gmail_thread_id=thread_id,
                        )
                        
                        try:
                            category, data = await self.agent.process_response(
                                entry, response_body=reply.get('body', '')
                            )
                            print(f"      ✅ Response: {category.value}")
                            followups_cancelled += 1
                            
                            # Apply label
                            await gmail.apply_label(reply.get('id'), "outreach/replied")
                            
                            # Update sheet status to "Replied"
                            row_number = followup.get('row_number')
                            if row_number and self.source == "sheets":
                                await self.integration.update_job_status(
                                    row_number, "Replied", datetime.now(timezone.utc)
                                )
                                print(f"      ✅ Sheet updated: Replied")
                            
                        except Exception as e:
                            print(f"      ⚠️  Error processing: {e}")
                            # Still cancel follow-ups
                            state.scheduled_followups = [
                                f for f in state.scheduled_followups 
                                if f.get('thread_id') != thread_id
                            ]
                            self.agent.memory.save_heartbeat_state(state)
                            followups_cancelled += 1
                            
            except Exception as e:
                print(f"   ⚠️  Error checking {company}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print("📊 Reply Check Complete")
        print(f"   Replies found: {replies_found}")
        print(f"   Follow-ups cancelled: {followups_cancelled}")
        print(f"{'='*60}")
    
    async def run_pending_followups(self, dry_run: bool = False, limit: int = None):
        """Check and send any due follow-ups."""
        print(f"\n{'='*60}")
        print("📅 Checking Pending Follow-ups")
        print(f"{'='*60}\n")
        
        state = self.agent.memory.load_heartbeat_state()
        now = datetime.now(timezone.utc)
        
        due_followups = []
        for task in state.scheduled_followups:
            if task.get('sent'):
                continue
            
            due_at_str = task.get('due_at', '')
            try:
                # Handle both timezone-aware and naive datetimes
                if due_at_str.endswith('Z'):
                    due_at = datetime.fromisoformat(due_at_str.replace('Z', '+00:00'))
                elif '+' in due_at_str or '-' in due_at_str[-6:]:
                    due_at = datetime.fromisoformat(due_at_str)
                else:
                    due_at = datetime.fromisoformat(due_at_str).replace(tzinfo=timezone.utc)
                
                if due_at <= now:
                    due_followups.append(task)
            except (ValueError, TypeError):
                continue
        
        if not due_followups:
            print("✅ No follow-ups due today")
            return
        
        if limit:
            due_followups = due_followups[:limit]
        
        print(f"📧 {len(due_followups)} follow-ups due:\n")
        
        for task in due_followups:
            company = task.get('company', 'Unknown')
            email = task.get('email', '')
            name = task.get('followup_name', 'Follow-up')
            
            print(f"   {name} for {company} ({email})")
            
            if dry_run:
                print("      🏃 DRY RUN - Would send\n")
                continue
            
            # In bulk mode, send without confirmation
            if self.bulk and email:
                # Add 5-second delay before sending
                print("      ⏱️  Waiting 5 seconds before sending...")
                await asyncio.sleep(5)
                
                success = await self._send_followup_email(task, name)
                if success:
                    task['sent'] = True
                    # Update sheet status
                    await self._update_followup_status(task, name)
                # Add small delay after send before next
                await asyncio.sleep(2)
                continue
            
            # Interactive mode
            confirm = input("      Send now? (yes/no): ").strip().lower()
            
            if confirm == "yes" and email:
                success = await self._send_followup_email(task, name)
                if success:
                    task['sent'] = True
                    # Update sheet status
                    await self._update_followup_status(task, name)
            else:
                print(f"      ❌ Skipped\n")
        
        # Save updated state
        self.agent.memory.save_heartbeat_state(state)
    
    async def _send_followup_email(self, task: dict, followup_name: str) -> bool:
        """Draft and send a follow-up email."""
        try:
            from mubot.memory.models import OutreachEntry, OutreachStatus
            from mubot.tools.gmail_client import GmailClient
            
            company = task.get('company', 'Unknown')
            role = task.get('role', 'Role')
            email = task.get('email', '')
            entry_id = task.get('entry_id', 'unknown')
            
            # Determine follow-up number
            if '1' in followup_name:
                followup_num = 1
            elif '2' in followup_name:
                followup_num = 2
            else:
                followup_num = 3
            
            # Create a minimal entry for follow-up generation
            original_entry = OutreachEntry(
                id=entry_id,
                company_name=company,
                role_title=role,
                recipient_email=email,
                recipient_name=task.get('recipient_name', ''),
                subject=f"Re: {role}",
                body=task.get('original_body', ''),
                status=OutreachStatus.SENT,
                followup_count=followup_num - 1,
            )
            
            # Draft follow-up
            print(f"      📝 Drafting {followup_name}...")
            
            # Get user profile info for sender details
            sender_name = self.agent.user_profile.name if self.agent.user_profile else "Muskan"
            sender_phone = self.agent.user_profile.phone if self.agent.user_profile else ""
            sender_linkedin = self.agent.user_profile.linkedin_url if self.agent.user_profile else ""
            
            # Get job description if available
            job_description = task.get('job_description', '')
            
            followup_body = await self.agent.reasoning.draft_followup(
                original_entry=original_entry,
                days_elapsed=4 if followup_num == 1 else (8 if followup_num == 2 else 10),
                job_description=job_description,
                recipient_name=task.get('recipient_name', 'Hiring Manager'),
                sender_name=sender_name,
                sender_phone=sender_phone,
                sender_linkedin=sender_linkedin,
            )
            
            # Parse subject and body from response
            subject = f"Re: {role}"
            body = followup_body
            
            # Try to extract subject if specified in response
            if followup_body.startswith("Subject:"):
                lines = followup_body.split('\n', 1)
                subject = lines[0].replace("Subject:", "").strip()
                body = lines[1].strip() if len(lines) > 1 else ""
            
            # Show preview
            print(f"      Subject: {subject}")
            print(f"      Body: {body[:100]}...")
            
            # In bulk mode, send without confirmation
            if self.bulk:
                # Send via Gmail
                gmail = GmailClient(self.agent.settings)
                authenticated = await gmail.authenticate()
                
                if not authenticated:
                    print("      ❌ Gmail authentication failed")
                    return False
                
                # Get thread ID if available
                thread_id = task.get('thread_id')
                
                result = await gmail.send_email(
                    to=email,
                    subject=subject,
                    body=body.replace('\n', '<br>'),
                    thread_id=thread_id,
                    apply_label=True
                )
                
                if result:
                    print(f"      ✅ {followup_name} sent successfully!")
                    return True
                else:
                    print(f"      ❌ Failed to send")
                    return False
            
            # Interactive mode - ask for confirmation
            confirm = input(f"      Send this {followup_name}? (yes/no): ").strip().lower()
            
            if confirm == "yes":
                # Send via Gmail
                gmail = GmailClient(self.agent.settings)
                authenticated = await gmail.authenticate()
                
                if not authenticated:
                    print("      ❌ Gmail authentication failed")
                    return False
                
                thread_id = task.get('thread_id')
                
                result = await gmail.send_email(
                    to=email,
                    subject=subject,
                    body=body.replace('\n', '<br>'),
                    thread_id=thread_id,
                    apply_label=True
                )
                
                if result:
                    print(f"      ✅ {followup_name} sent successfully!")
                    return True
                else:
                    print(f"      ❌ Failed to send")
                    return False
            else:
                print(f"      ❌ Cancelled")
                return False
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            import traceback
            traceback.print_exc()
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
        help="Bulk mode - no confirmations"
    )
    parser.add_argument(
        "--check-replies",
        action="store_true",
        help="Check Gmail for replies and cancel follow-ups (automated response tracking)"
    )
    
    args = parser.parse_args()
    
    async def run():
        campaign = AutomatedCampaign(source=args.source, bulk=args.bulk)
        await campaign.initialize()
        
        if args.check_replies:
            print(f"\n{'='*60}")
            print("📥 Checking for Email Replies")
            print(f"{'='*60}\n")
            await campaign.check_for_replies()
            return
        
        if args.followups_only:
            await campaign.run_pending_followups(dry_run=args.dry_run)
        else:
            await campaign.run_campaign(limit=args.limit, dry_run=args.dry_run)
            await campaign.run_pending_followups(dry_run=args.dry_run)
    
    asyncio.run(run())


if __name__ == "__main__":
    main()

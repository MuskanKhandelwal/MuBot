#!/usr/bin/env python3
"""
Heartbeat Runner Script

This script runs the MuBot heartbeat manually or as a scheduled job.
The heartbeat performs:
1. Checks for pending follow-ups
2. Scans for email replies
3. Generates daily summaries
4. Updates tracking data

Usage:
    # Run once immediately
    python -m scripts.run_heartbeat
    
    # Or if installed
    mubot-heartbeat
    
    # Add to crontab for daily runs
    0 9 * * * cd /path/to/mubot && python -m scripts.run_heartbeat
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file explicitly before importing mubot modules
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent.parent  # Go up to project root
load_dotenv(project_root / ".env")


def check_token_valid(token_path: Path) -> bool:
    """Check if Gmail token exists and is valid."""
    if not token_path.exists():
        return False
    
    try:
        import pickle
        with open(token_path, "rb") as f:
            creds = pickle.load(f)
        
        if creds and creds.valid:
            return True
        
        if creds and creds.expired and creds.refresh_token:
            # Try to refresh
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            # Save refreshed token
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
            return True
        
        return False
    except Exception as e:
        print(f"   Token check error: {e}")
        return False


async def check_inbox_for_replies(agent, gmail_client):
    """
    Check Gmail for replies to sent outreach emails.
    
    Uses thread_id stored in heartbeat-state.json to check each
    conversation for new replies. If replies are found, processes
    them and cancels scheduled follow-ups.
    
    Also searches Gmail for any replies that might be in different threads.
    
    Returns:
        Tuple of (replies_found_count, followups_cancelled_count)
    """
    from mubot.memory.models import OutreachEntry, OutreachStatus
    
    state = agent.memory.load_heartbeat_state()
    all_followups = state.scheduled_followups
    
    # Check ALL unsent follow-ups
    # (A reply could come before the follow-up is due)
    unsent_followups = [f for f in all_followups if not f.get('sent', False)]
    followups_with_threads = [f for f in unsent_followups if f.get('thread_id')]
    followups_without_threads = [f for f in unsent_followups if not f.get('thread_id')]
    
    if not unsent_followups:
        print("   No unsent follow-ups to check")
        return 0, 0
    
    # Get unique companies to search for (from ALL unsent follow-ups)
    companies = set(f.get('company', '').strip() for f in unsent_followups if f.get('company'))
    print(f"   Checking {len(unsent_followups)} follow-ups ({len(companies)} companies)")
    print(f"   - {len(followups_with_threads)} have thread_ids")
    print(f"   - {len(followups_without_threads)} will be searched by company name")
    
    replies_found = 0
    followups_cancelled = 0
    processed_threads = set()  # Track processed threads to avoid duplicates
    
    # Method 1: Check stored thread_ids
    print(f"   Method 1: Checking {len(set(f.get('thread_id') for f in followups_with_threads))} stored threads...")
    
    for followup in followups_with_threads:
        thread_id = followup.get('thread_id')
        company = followup.get('company', 'Unknown')
        entry_id = followup.get('entry_id')
        
        if thread_id in processed_threads:
            continue
        processed_threads.add(thread_id)
        
        try:
            # Get all messages in the thread
            messages = await gmail_client.get_replies(thread_id)
            
            if len(messages) > 1:  # More than just our original message
                # Filter to only incoming messages (not from us)
                sender_email = agent.user_profile.email if agent.user_profile else ""
                sender_domain = sender_email.split('@')[-1] if '@' in sender_email else ""
                
                incoming = []
                for m in messages:
                    from_addr = m.get('from', '')
                    # Skip messages from ourselves
                    if sender_email and sender_email in from_addr:
                        continue
                    if sender_domain and f"@{sender_domain}" in from_addr:
                        continue
                    incoming.append(m)
                
                if incoming:
                    # Found a reply!
                    reply = incoming[-1]  # Get the most recent reply
                    replies_found += 1
                    
                    print(f"   📨 Reply from {company}!")
                    print(f"      From: {reply.get('from', 'Unknown')}")
                    print(f"      Subject: {reply.get('subject', 'No subject')}")
                    preview = reply.get('body', '')[:100].replace('\n', ' ')
                    print(f"      Preview: {preview}...")
                    
                    # Create a minimal OutreachEntry for processing
                    entry = OutreachEntry(
                        id=entry_id or f"temp-{thread_id}",
                        company_name=company,
                        role_title=followup.get('role', 'Role'),
                        recipient_email=followup.get('email', ''),
                        recipient_name=followup.get('recipient_name', 'Hiring Manager'),
                        subject=reply.get('subject', f"Re: {followup.get('role', 'Role')} at {company}"),
                        body="",  # Original body not needed for processing
                        status=OutreachStatus.SENT,
                        gmail_thread_id=thread_id,
                    )
                    
                    # Process the response (this auto-cancels follow-ups)
                    try:
                        category, data = await agent.process_response(
                            entry,
                            response_body=reply.get('body', '')
                        )
                        print(f"      ✅ Response processed: {category.value}")
                        print(f"      ✅ Follow-ups cancelled for {company}")
                        followups_cancelled += 1
                        
                        # Apply 'replied' label in Gmail to the reply message
                        reply_message_id = reply.get('id')
                        if reply_message_id:
                            await gmail_client.apply_label(reply_message_id, "outreach/replied")
                        
                    except Exception as e:
                        print(f"      ⚠️  Error processing response: {e}")
                        # Still cancel follow-ups to be safe
                        state.scheduled_followups = [
                            f for f in state.scheduled_followups 
                            if f.get('thread_id') != thread_id
                        ]
                        agent.memory.save_heartbeat_state(state)
                        followups_cancelled += 1
        
        except Exception as e:
            print(f"   ⚠️  Error checking thread for {company}: {e}")
            continue
    
    # Method 2: Search Gmail for replies to companies with scheduled follow-ups
    print(f"   Method 2: Searching Gmail for replies to {len(companies)} companies...")
    
    for company in companies:
        if not company:
            continue
            
        try:
            # Search for emails from this company
            search_query = f"from:{company.replace(' ', '')} OR from:{company.split()[0]}"
            search_results = await gmail_client.search_messages(search_query, max_results=10)
            
            for msg_meta in search_results:
                thread_id = msg_meta.get('threadId')
                if not thread_id or thread_id in processed_threads:
                    continue
                
                # Get the full message
                msg = await gmail_client.get_message(msg_meta['id'])
                if not msg:
                    continue
                
                # Check if this is a reply to one of our emails
                from_addr = msg.get('from', '')
                subject = msg.get('subject', '')
                
                # Skip if from us
                sender_email = agent.user_profile.email if agent.user_profile else ""
                if sender_email and sender_email in from_addr:
                    continue
                
                # Check if subject contains "Re:" indicating it's a reply
                if 'Re:' in subject:
                    # Get all messages in thread to confirm we sent original
                    thread_messages = await gmail_client.get_replies(thread_id)
                    
                    # Check if we sent the original message in this thread
                    we_sent_original = any(
                        sender_email in m.get('from', '')
                        for m in thread_messages
                    )
                    
                    if we_sent_original and len(thread_messages) > 1:
                        # This is a reply to us!
                        processed_threads.add(thread_id)
                        replies_found += 1

                        print(f"   📨 Reply found via search from {company}!")
                        print(f"      From: {from_addr}")
                        print(f"      Subject: {subject}")
                        preview = msg.get('body', '')[:100].replace('\n', ' ')
                        print(f"      Preview: {preview}...")

                        # Cancel only follow-ups for THIS thread, not the whole company
                        cancelled = 0
                        new_followups = []
                        matched_followup = None
                        for f in state.scheduled_followups:
                            if f.get('thread_id') == thread_id and not f.get('sent', False):
                                cancelled += 1
                                matched_followup = matched_followup or f
                            else:
                                new_followups.append(f)

                        state.scheduled_followups = new_followups
                        agent.memory.save_heartbeat_state(state)
                        followups_cancelled += cancelled

                        print(f"      ✅ Cancelled {cancelled} follow-ups for this thread ({company})")

                        # Log to learnings tracker
                        try:
                            from mubot.memory.learnings import LearningsTracker
                            from mubot.memory.models import OutreachEntry, OutreachStatus, ResponseCategory
                            fu = matched_followup or {}
                            log_entry = OutreachEntry(
                                id=fu.get('entry_id', f"search-{thread_id}"),
                                company_name=company,
                                role_title=fu.get('role', 'Unknown'),
                                recipient_email=fu.get('email', ''),
                                recipient_name=fu.get('recipient_name', ''),
                                subject=subject,
                                body="",
                                status=OutreachStatus.REPLIED,
                                gmail_thread_id=thread_id,
                            )
                            body_text = msg.get('body', '')
                            LearningsTracker(agent.memory.base_path).log_response(
                                log_entry, ResponseCategory.NEUTRAL, body_text
                            )
                        except Exception:
                            pass

                        # Apply label
                        await gmail_client.apply_label(msg['id'], "outreach/replied")
                        
        except Exception as e:
            print(f"   ⚠️  Error searching for {company}: {e}")
            continue
    
    return replies_found, followups_cancelled


async def run_heartbeat():
    """Run the heartbeat process."""
    from mubot.agent import JobSearchAgent
    from mubot.tools import Scheduler
    from mubot.config import get_settings
    from mubot.tools.gmail_client import GmailClient
    
    print("=" * 60)
    print("🤖 MuBot Heartbeat Runner")
    print("=" * 60)
    
    settings = get_settings()
    
    # Initialize agent
    agent = JobSearchAgent()
    initialized = await agent.initialize()
    
    if not initialized:
        print("\n✗ Failed to initialize agent.")
        print("Make sure you've run 'mubot-init' first.")
        return 1
    
    # Create and run scheduler
    scheduler = Scheduler(settings, agent.memory, agent)
    await scheduler.start()
    
    try:
        # Run heartbeat
        print("\n💓 Running daily heartbeat")
        print("=" * 60)
        
        # Check for pending follow-ups
        pending = agent.memory.get_pending_followups()
        all_followups = agent.memory.load_heartbeat_state().scheduled_followups
        unsent = [f for f in all_followups if not f.get('sent', False)]
        print(f"📬 {len(pending)} follow-ups due now, {len(unsent)} total scheduled")
        
        # Check inbox for replies (NEW!)
        print("\n📥 Checking inbox for replies...")
        try:
            # Ensure credentials path is absolute from project root
            project_root = Path(__file__).parent.parent.parent.parent
            settings.gmail_credentials_path = project_root / settings.gmail_credentials_path
            settings.gmail_token_path = project_root / settings.gmail_token_path
            
            # Check token validity first (non-interactive)
            token_valid = check_token_valid(settings.gmail_token_path)
            
            if not token_valid:
                print("   ⚠️  Gmail not authenticated or token expired")
                print("   Run 'python reauth_gmail.py' to re-authenticate")
                print("   Skipping inbox check")
            else:
                # Token is valid, authenticate and check inbox
                gmail = GmailClient(settings)
                authenticated = await gmail.authenticate()
                
                if authenticated:
                    replies_found, followups_cancelled = await check_inbox_for_replies(agent, gmail)
                    if replies_found:
                        print(f"\n   📨 Found {replies_found} new replies")
                        print(f"   ✅ Cancelled {followups_cancelled} follow-ups")
                    else:
                        print("   ✓ No new replies")
                else:
                    print("   ⚠️  Gmail authentication failed - skipping inbox check")
                
        except Exception as e:
            print(f"   ⚠️  Error checking inbox: {e}")
        
        # Generate daily summary
        print("\n📊 Generating summary...")
        try:
            summary = await agent.get_daily_summary()
            print("\n" + summary)
        except Exception as e:
            print(f"   ⚠️  Error generating summary: {e}")
        
        # Update heartbeat state
        state = agent.memory.load_heartbeat_state()
        state.last_run = datetime.now(timezone.utc)
        agent.memory.save_heartbeat_state(state)
        
        print("\n" + "=" * 60)
        print("💓 Heartbeat complete")
        print("=" * 60)
        
        print("\n✓ Heartbeat completed successfully")
        return 0
        
    except Exception as e:
        print(f"\n✗ Heartbeat failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await scheduler.stop()


def main():
    """Entry point."""
    try:
        exit_code = asyncio.run(run_heartbeat())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()

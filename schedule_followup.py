#!/usr/bin/env python3
"""
Quick script to schedule follow-ups for sent emails.

Usage:
    python schedule_followup.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mubot.agent import JobSearchAgent


async def main():
    """Interactive follow-up scheduler."""
    print("=" * 70)
    print("📅 Follow-Up Scheduler")
    print("=" * 70)
    print()
    
    agent = JobSearchAgent()
    await agent.initialize()
    
    # Show current stats
    stats = agent.memory.get_daily_stats()
    pending = agent.memory.get_pending_followups()
    
    print(f"📊 Today's emails sent: {stats.emails_sent}")
    print(f"📅 Pending follow-ups: {len(pending)}")
    print()
    
    if pending:
        print("Current pending follow-ups:")
        for i, task in enumerate(pending[:5], 1):
            company = task.get('company', 'Unknown')
            due = task.get('due_at', 'Unknown')
            print(f"  {i}. {company} - Due: {due}")
        print()
    
    # Get company name
    company = input("Company name for follow-up: ").strip()
    if not company:
        print("❌ Company name required")
        return
    
    # Get days delay
    days_input = input("Days until follow-up (default 5): ").strip()
    days = int(days_input) if days_input.isdigit() else 5
    
    # Check if we have an entry for this company
    from mubot.memory.models import OutreachEntry, OutreachStatus
    
    # Create a minimal entry for scheduling
    entry = OutreachEntry(
        id=f"manual-{datetime.utcnow().timestamp()}",
        recipient_email="pending@example.com",  # Will be updated
        company_name=company,
        role_title="Role",
        subject=f"Follow-up for {company}",
        body="Follow-up email body",
        status=OutreachStatus.SENT,
        sent_at=datetime.utcnow(),
    )
    
    # Schedule follow-up
    success, msg = await agent.schedule_followup(entry, days_delay=days)
    
    if success:
        print(f"\n✅ {msg}")
        
        # Show calculation
        followup_date = datetime.utcnow() + timedelta(days=days)
        print(f"📅 Follow-up will be sent on: {followup_date.strftime('%Y-%m-%d')}")
        
        print(f"""
💡 What happens next:
1. The follow-up is saved to your memory
2. Run 'python -m scripts.run_heartbeat' daily to check
3. Or use the chat: "Check follow-ups"
4. The follow-up will be sent automatically on {followup_date.strftime('%Y-%m-%d')}

To check all pending follow-ups:
  python mubot_chat_enhanced.py
  → Type: "Check follow-ups"
""")
    else:
        print(f"\n❌ {msg}")


if __name__ == "__main__":
    asyncio.run(main())

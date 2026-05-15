#!/usr/bin/env python3
"""
Automated Reply Checker

Runs every hour to check for email replies and auto-cancels follow-ups.
This keeps your follow-up list clean and prevents sending follow-ups
to people who have already responded.

Usage:
    # Run once
    python scripts/schedule_replies.py
    
    # Add to crontab (runs every hour)
    0 * * * * cd /path/to/mubot && python scripts/schedule_replies.py >> logs/replies.log 2>&1
    
    # Or run via auto_campaign.py
    python auto_campaign.py --check-replies
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mubot.agent import JobSearchAgent
from integrations.google_sheets import GoogleSheetsIntegration


async def check_replies():
    """Check for replies and update follow-ups."""
    print("=" * 60)
    print("🤖 MuBot Auto Reply Checker")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    # Initialize agent
    agent = JobSearchAgent()
    initialized = await agent.initialize()
    
    if not initialized:
        print("\n✗ Failed to initialize agent")
        return 1
    
    # Create sheets integration
    sheets = GoogleSheetsIntegration(
        credentials_path="./credentials/sheets_credentials.json",
        spreadsheet_name="Job Applications"
    )
    
    # Import and run reply check from auto_campaign
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from auto_campaign import AutomatedCampaign
    
    campaign = AutomatedCampaign(source="sheets", bulk=True)
    campaign.agent = agent
    campaign.integration = sheets
    
    await campaign.check_for_replies()
    
    print("\n✅ Done!")
    return 0


def main():
    """Entry point."""
    try:
        exit_code = asyncio.run(check_replies())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

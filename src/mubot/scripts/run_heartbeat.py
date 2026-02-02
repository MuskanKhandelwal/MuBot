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
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def run_heartbeat():
    """Run the heartbeat process."""
    from mubot.agent import JobSearchAgent
    from mubot.tools import Scheduler
    from mubot.config import get_settings
    
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
        await scheduler.run_heartbeat_now()
        print("\n✓ Heartbeat completed successfully")
        return 0
    except Exception as e:
        print(f"\n✗ Heartbeat failed: {e}")
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

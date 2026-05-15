#!/usr/bin/env python3
"""
MuBot — Your Job Search Bot

Usage:
    python mubot.py            # Start interactive bot
    python mubot.py campaign   # Run bulk campaign (same as auto_campaign.py --bulk)
    python mubot.py followups  # Send due follow-ups
    python mubot.py replies    # Check for replies
    python mubot.py status     # Show status and exit
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mubot.agent.bot import MuBot


async def main():
    args = sys.argv[1:]
    bot = MuBot()

    # Quick one-shot commands (no interactive loop)
    if args:
        cmd = args[0].lower()

        if cmd == "campaign":
            if not await bot.initialize():
                sys.exit(1)
            limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
            print(await bot._run_campaign(limit=limit))
            return

        if cmd == "followups":
            if not await bot.initialize():
                sys.exit(1)
            print(await bot._run_followups())
            return

        if cmd == "replies":
            if not await bot.initialize():
                sys.exit(1)
            print(await bot._check_replies())
            return

        if cmd == "status":
            if not await bot.initialize():
                sys.exit(1)
            print(bot._show_status())
            return

    # Default: interactive bot
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye!")

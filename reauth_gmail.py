#!/usr/bin/env python3
"""Quick script to re-authenticate Gmail."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mubot.tools.gmail_client import GmailClient
from mubot.config import get_settings
import asyncio

async def main():
    print("🔐 Re-authenticating Gmail...")
    settings = get_settings()
    gmail = GmailClient(settings)
    success = await gmail.authenticate()
    if success:
        print("✅ Gmail authentication successful!")
    else:
        print("❌ Authentication failed")

if __name__ == "__main__":
    asyncio.run(main())

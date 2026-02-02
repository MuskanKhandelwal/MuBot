#!/usr/bin/env python3
"""
Interactive MuBot - Talk to your job search assistant!

Usage:
    python interactive_bot.py

Examples of what you can say:
    "Draft a cold email for the Data Scientist role at Meta"
    "Add Google to my pipeline as a Data Scientist"
    "Show my pipeline"
    "Show my daily summary"
    "What do I know about Netflix?"
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mubot.agent import JobSearchAgent
from mubot.agent.nlp_interface import NLExecutor


async def main():
    """Interactive chat with MuBot."""
    print("=" * 60)
    print("🤖 MuBot - Your Job Search Assistant")
    print("=" * 60)
    print()
    
    # Initialize
    print("🔄 Initializing...")
    agent = JobSearchAgent()
    initialized = await agent.initialize()
    
    if not initialized:
        print("❌ Failed to initialize. Run: python -m mubot.scripts.init_project")
        return
    
    executor = NLExecutor(agent)
    print(f"✅ Ready! Hello, {agent.user_profile.name}!")
    print()
    
    print("I can help you:")
    print("  • Draft personalized cold emails")
    print("  • Track job applications in your pipeline")
    print("  • Schedule follow-ups")
    print("  • Check for replies")
    print()
    print("Example commands:")
    print('  "Draft an email for the Data Scientist role at Meta"')
    print('  "Add Google to my pipeline"')
    print('  "Show my pipeline"')
    print('  "Show my daily summary"')
    print()
    print("Type 'exit' or 'quit' to leave")
    print("=" * 60)
    print()
    
    # Main loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nGood luck with your job search! 👋")
                break
            
            if not user_input:
                continue
            
            # Execute command
            response = await executor.execute(user_input)
            print(f"🤖 MuBot: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except EOFError:
            break


if __name__ == "__main__":
    asyncio.run(main())

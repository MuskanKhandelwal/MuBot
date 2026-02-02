#!/usr/bin/env python3
"""
Enhanced MuBot Chat - With Job Description Support!

Usage:
    python mubot_chat_enhanced.py

Features:
    • Natural language commands
    • Multi-turn JD collection (paste full job descriptions!)
    • JD-optimized email drafting
    • Interactive recipient collection

Examples:
    "Draft an email for the Data Scientist role at Netflix"
    → Bot asks for JD → Paste JD → Bot asks for recipient → Get optimized email!
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mubot.agent import JobSearchAgent
from mubot.agent.nlp_interface_enhanced import EnhancedNLExecutor


async def main():
    """Enhanced interactive chat with JD support."""
    print("=" * 70)
    print("🤖 MuBot - Enhanced Chat (with JD Support!)")
    print("=" * 70)
    print()
    
    # Initialize
    print("🔄 Initializing...")
    agent = JobSearchAgent()
    initialized = await agent.initialize()
    
    if not initialized:
        print("❌ Failed to initialize. Run: python -m mubot.scripts.init_project")
        return
    
    executor = EnhancedNLExecutor(agent)
    print(f"✅ Ready! Hello, {agent.user_profile.name}!")
    print()
    
    print("I can help you:")
    print("  • Draft personalized cold emails with JD optimization")
    print("  • Track job applications")
    print("  • Check your pipeline")
    print()
    print("💡 NEW: Just say 'Draft an email for [role] at [company]'")
    print("   and I'll guide you through pasting the JD!")
    print()
    print("Type 'exit' or 'quit' to leave")
    print("=" * 70)
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
            
            # Only print if there's a response (some states are silent)
            if response:
                print(f"🤖 MuBot: {response}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except EOFError:
            break


if __name__ == "__main__":
    asyncio.run(main())

"""
MuBot Interactive Mode

Consolidates interactive chat functionality from:
- interactive_bot.py (basic NLP interface)
- mubot_chat_enhanced.py (enhanced with JD support)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mubot.agent import JobSearchAgent


class InteractiveMode:
    """Interactive chat mode for MuBot."""
    
    def __init__(self, enhanced: bool = True):
        self.enhanced = enhanced
        self.agent: JobSearchAgent = None
        self.executor = None
        
    async def initialize(self):
        """Initialize the agent and executor."""
        print("=" * 70)
        if self.enhanced:
            print("🤖 MuBot - Interactive Chat (with JD Support!)")
        else:
            print("🤖 MuBot - Your Job Search Assistant")
        print("=" * 70)
        print()
        
        print("🔄 Initializing...")
        self.agent = JobSearchAgent()
        initialized = await self.agent.initialize()
        
        if not initialized:
            print("❌ Failed to initialize. Run: python -m mubot.scripts.init_project")
            return False
        
        # Import the appropriate executor
        if self.enhanced:
            from mubot.agent.nlp_interface_enhanced import EnhancedNLExecutor
            self.executor = EnhancedNLExecutor(self.agent)
        else:
            from mubot.agent.nlp_interface import NLExecutor
            self.executor = NLExecutor(self.agent)
        
        print(f"✅ Ready! Hello, {self.agent.user_profile.name}!")
        print()
        
        self._print_help()
        print("=" * 70)
        print()
        
        return True
    
    def _print_help(self):
        """Print available commands."""
        print("I can help you:")
        
        if self.enhanced:
            print("  • Draft personalized cold emails with JD optimization")
            print("  • Track job applications")
            print("  • Check your pipeline")
            print()
            print("💡 NEW: Just say 'Draft an email for [role] at [company]'")
            print("   and I'll guide you through pasting the JD!")
        else:
            print("  • Draft personalized cold emails")
            print("  • Track job applications in your pipeline")
            print("  • Schedule follow-ups")
            print("  • Check for replies")
            print()
            print("Example commands:")
            print('  "Draft an email for the Data Scientist role at Meta"')
            print('  "Add Google to my pipeline"')
            print('  "Show my daily summary"')
        
        print()
        print("Type 'exit' or 'quit' to leave")
    
    async def run(self):
        """Run the interactive loop."""
        if not await self.initialize():
            return 1
        
        # Main loop
        while True:
            try:
                user_input = input("💬 You: ").strip()
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\nGood luck with your job search! 👋")
                    break
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ["help", "?"]:
                    self._print_help()
                    continue
                
                # Execute command
                if self.enhanced:
                    response = await self._execute_enhanced(user_input)
                else:
                    response = await self.executor.execute(user_input)
                
                # Only print if there's a response (some states are silent)
                if response:
                    print(f"🤖 MuBot: {response}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except EOFError:
                break
        
        return 0
    
    async def _execute_enhanced(self, user_input: str) -> str:
        """Execute with enhanced executor, handling special states."""
        from mubot.agent.nlp_interface_enhanced import ConversationState
        
        # Check if we're in a multi-turn conversation
        if self.executor.state == ConversationState.COLLECTING_JD:
            return await self.executor._handle_jd_input(user_input)
        
        if self.executor.state == ConversationState.COLLECTING_RECIPIENT:
            return await self.executor._handle_recipient_input(user_input)
        
        if self.executor.state == ConversationState.CONFIRMING_SEND:
            return await self.executor._handle_confirmation_input(user_input)
        
        # Check for confirmation responses first
        confirmation_response = await self.executor.handle_confirmation(user_input)
        if confirmation_response is not None:
            return confirmation_response
        
        # Normal command execution
        return await self.executor.execute(user_input)


async def run_interactive(enhanced: bool = True):
    """Run interactive mode."""
    mode = InteractiveMode(enhanced=enhanced)
    return await mode.run()

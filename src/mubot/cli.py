#!/usr/bin/env python3
"""
Interactive CLI for MuBot

This module provides a conversational interface to MuBot.
Users can type natural language commands and the agent will execute them.

Usage:
    mubot-chat          # After pip install
    python -m cli       # Direct execution
    python cli.py       # Direct execution

Features:
- Natural language command parsing
- Conversation history
- Context-aware responses
- Help system
"""

import asyncio
import sys
from pathlib import Path

# Try to import rich for pretty output, fallback to plain print
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from mubot.agent import JobSearchAgent
from mubot.agent.nlp_interface import NLExecutor


class MuBotCLI:
    """
    Interactive command-line interface for MuBot.
    
    Provides a chat-like experience where users can:
    - Type natural language commands
    - Get context-aware responses
    - Maintain conversation state
    """
    
    def __init__(self):
        self.agent: JobSearchAgent = None
        self.executor: NLExecutor = None
        self.console = Console() if HAS_RICH else None
        self.conversation_history = []
        self.running = False
    
    def print(self, message: str, style: str = None):
        """Print with optional styling."""
        if self.console and HAS_RICH:
            if style:
                self.console.print(message, style=style)
            else:
                self.console.print(message)
        else:
            print(message)
    
    def print_welcome(self):
        """Display welcome message."""
        welcome_text = """
🤖 **Welcome to MuBot - Your Job Search Assistant**

I can help you:
• Draft personalized cold emails
• Track your job applications
• Schedule follow-ups
• Monitor replies
• Manage your pipeline

**Get started:** Try saying "Draft an email for the engineer role at Google"
**Need help?** Type "help" anytime

Type "exit" or "quit" to leave.
"""
        if self.console and HAS_RICH:
            self.console.print(Panel(Markdown(welcome_text), title="MuBot", border_style="blue"))
        else:
            print("=" * 60)
            print("🤖 Welcome to MuBot - Your Job Search Assistant")
            print("=" * 60)
            print("\nI can help you:")
            print("• Draft personalized cold emails")
            print("• Track your job applications")
            print("• Schedule follow-ups")
            print("\nGet started: Try saying 'Draft an email for Google'")
            print("Need help: Type 'help'")
            print("\nType 'exit' or 'quit' to leave.")
            print("=" * 60)
    
    def print_prompt(self):
        """Print the input prompt."""
        if self.console and HAS_RICH:
            self.console.print("\n[bold blue]You:[/bold blue] ", end="")
        else:
            print("\nYou: ", end="")
    
    def print_response(self, response: str):
        """Print MuBot's response."""
        if self.console and HAS_RICH:
            # Check if response has markdown
            if any(c in response for c in ['*', '#', '-', '`']):
                self.console.print(Panel(Markdown(response), title="🤖 MuBot", border_style="green"))
            else:
                self.console.print(f"[bold green]🤖 MuBot:[/bold green] {response}")
        else:
            print(f"\n🤖 MuBot: {response}")
    
    async def initialize(self):
        """Initialize the agent and NLP interface."""
        self.print("Initializing...", style="dim")
        
        self.agent = JobSearchAgent()
        initialized = await self.agent.initialize()
        
        if not initialized:
            self.print("\n❌ Failed to initialize MuBot.", style="bold red")
            self.print("\nPlease run: mubot-init", style="yellow")
            return False
        
        self.executor = NLExecutor(self.agent)
        
        # Load user name if available
        user = self.agent.user_profile
        if user and user.name:
            self.print(f"\n👋 Hello, {user.name}!", style="bold green")
        
        return True
    
    async def process_input(self, user_input: str) -> bool:
        """
        Process user input.
        
        Returns:
            False if user wants to exit
        """
        user_input = user_input.strip()
        
        if not user_input:
            return True
        
        # Add to history
        self.conversation_history.append(("user", user_input))
        
        # Check for exit commands
        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            self.print_response("Good luck with your job search! 👋")
            return False
        
        # Check for confirmation response (yes/no after prompts)
        confirmation_result = await self.executor.handle_confirmation(user_input)
        if confirmation_result:
            self.print_response(confirmation_result)
            return True
        
        # Process through NLP interface
        try:
            response = await self.executor.execute(user_input)
            self.print_response(response)
            self.conversation_history.append(("bot", response))
            
        except Exception as e:
            self.print_response(f"❌ Sorry, something went wrong: {str(e)}")
        
        return True
    
    async def run(self):
        """Main loop."""
        self.print_welcome()
        
        # Initialize
        if not await self.initialize():
            return
        
        self.running = True
        
        # Main loop
        while self.running:
            self.print_prompt()
            
            try:
                user_input = input()
            except EOFError:
                break
            except KeyboardInterrupt:
                self.print("\n\nGoodbye! 👋")
                break
            
            should_continue = await self.process_input(user_input)
            if not should_continue:
                break
        
        # Cleanup
        if self.agent:
            # Any cleanup needed
            pass


async def main_async():
    """Async entry point."""
    cli = MuBotCLI()
    await cli.run()


def main():
    """Entry point for CLI commands."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

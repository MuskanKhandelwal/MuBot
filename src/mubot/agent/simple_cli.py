#!/usr/bin/env python3
"""
Simple Interactive CLI for MuBot

A straightforward command-line interface without complex NLP.
Just type commands in a simple format.

Usage:
    python -m mubot.simple_cli
"""

import asyncio
import shlex
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from mubot import JobSearchAgent
from mubot.pipelines import JobPipeline, PipelineStage


class SimpleMuBotCLI:
    """Simple command-line interface for MuBot."""
    
    def __init__(self):
        self.agent = None
        self.pipeline = None
        self.console = Console() if HAS_RICH else None
        self.last_draft = None
        
    def print(self, message: str, style: str = None):
        """Print with optional styling."""
        if self.console and HAS_RICH:
            if style:
                self.console.print(message, style=style)
            else:
                self.console.print(message)
        else:
            print(message)
    
    def print_header(self):
        """Display welcome message."""
        welcome = """
🤖 MuBot - Job Search Assistant

Quick Commands:
  draft <company> <role> [name] [email]  - Draft a cold email
  add <company> <role>                   - Add to pipeline  
  pipeline                               - Show your pipeline
  summary                                - Daily summary
  send                                   - Send last draft (asks confirm)
  help                                   - Show all commands
  exit                                   - Quit

Examples:
  draft Spotify "Data Scientist" "Alex Johnson" alex@spotify.com
  add Meta "Software Engineer"
  pipeline
"""
        if self.console and HAS_RICH:
            self.console.print(Panel(welcome, title="MuBot", border_style="blue"))
        else:
            print(welcome)
    
    async def initialize(self):
        """Initialize the agent."""
        self.print("Initializing...", style="dim")
        
        self.agent = JobSearchAgent()
        success = await self.agent.initialize()
        
        if not success:
            self.print("❌ Failed to initialize. Run 'mubot-init' first.", style="bold red")
            return False
        
        self.pipeline = JobPipeline(self.agent.memory)
        
        user = self.agent.user_profile
        if user and user.name:
            self.print(f"👋 Hello, {user.name}!", style="bold green")
        
        return True
    
    def print_draft(self, draft):
        """Print email draft nicely."""
        self.print(f"\n{'='*60}")
        self.print(f"✉️  EMAIL DRAFT")
        self.print(f"{'='*60}")
        self.print(f"To: {draft.recipient_name or 'Hiring Manager'} <{draft.recipient_email or 'Not set'}>")
        self.print(f"Subject: {draft.subject}")
        self.print(f"{'='*60}")
        self.print(draft.body)
        self.print(f"{'='*60}")
        
        if draft.personalization_elements:
            self.print(f"\n📝 Personalization:")
            for elem in draft.personalization_elements:
                self.print(f"  • {elem}")
    
    async def handle_draft(self, args):
        """Handle draft command with interactive prompts."""
        # If args provided, try to use them
        if len(args) >= 2:
            company = args[0]
            # Join remaining args until we detect an email or run out
            role_parts = []
            name = None
            email = None
            
            for i, arg in enumerate(args[1:], 1):
                if '@' in arg and '.' in arg:
                    # This looks like an email
                    email = arg
                    # Everything between role and email is the name
                    if i > 1:
                        name = ' '.join(args[1:i])
                    break
                else:
                    role_parts.append(arg)
            
            if not role_parts:
                role = args[1]
            else:
                role = ' '.join(role_parts)
        else:
            # Interactive mode
            self.print("📝 Creating new email draft...")
            company = input("Company name: ").strip()
            if not company:
                self.print("❌ Company name required")
                return
            
            role = input("Job title (e.g., 'Data Scientist'): ").strip()
            if not role:
                self.print("❌ Job title required")
                return
            
            name = input("Recipient name (optional): ").strip() or None
            email = input("Recipient email (optional): ").strip() or None
        
        self.print(f"📝 Drafting email for {role} at {company}...")
        
        draft, warnings = await self.agent.draft_email(
            company_name=company,
            role_title=role,
            company_context=f"{company} - innovative company",  # Generic context
            recipient_name=name,
            recipient_email=email,
        )
        
        self.last_draft = draft
        self.print_draft(draft)
        
        if warnings:
            self.print(f"\n⚠️  Warnings:")
            for w in warnings:
                self.print(f"  • {w}")
        
        self.print(f"\n💡 Type 'send' to send, or 'draft' to create another")
    
    async def handle_send(self, args):
        """Handle send command."""
        if not self.last_draft:
            self.print("❌ No draft to send. Create one first with 'draft'")
            return
        
        draft = self.last_draft
        
        self.print(f"\n🚀 Ready to send to {draft.recipient_name or draft.company_name}")
        self.print(f"Subject: {draft.subject}")
        
        if not draft.recipient_email:
            email = input("Recipient email: ").strip()
            if not email:
                self.print("❌ Email required")
                return
            draft.recipient_email = email
        
        confirm = input(f"\nSend to {draft.recipient_email}? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            success, msg = await self.agent.send_email(draft, approved=True)
            if success:
                self.print(f"✅ {msg}")
                self.pipeline.link_outreach(
                    self.pipeline.add_opportunity(draft.company_name, draft.role_title).id,
                    draft
                )
                self.last_draft = None
            else:
                self.print(f"❌ {msg}")
        else:
            self.print("❌ Send cancelled")
    
    async def handle_add(self, args):
        """Handle add command."""
        if len(args) < 2:
            self.print("❌ Usage: add <company> <role>")
            return
        
        company = args[0]
        role = args[1]
        
        opp = self.pipeline.add_opportunity(company_name=company, role_title=role)
        self.print(f"✅ Added {company} - {role} to pipeline (ID: {opp.id[:8]})")
    
    async def handle_pipeline(self, args):
        """Handle pipeline command."""
        summary = self.pipeline.get_pipeline_summary()
        self.print(summary)
    
    async def handle_summary(self, args):
        """Handle summary command."""
        stats = self.agent.memory.get_daily_stats()
        self.print(f"\n📊 Today's Summary")
        self.print(f"   Emails sent: {stats.emails_sent}/{self.agent.settings.max_daily_emails}")
        self.print(f"   Replies: {stats.replies_received}")
        self.print(f"   Positive: {stats.positive_responses}")
    
    async def handle_help(self):
        """Show help."""
        help_text = """
Available Commands:

DRAFTING
  draft <company> <role> [name] [email]  - Draft a cold email
  send                                     - Send last draft (asks confirm)

PIPELINE
  add <company> <role>                   - Add opportunity to pipeline
  pipeline                               - Show all opportunities
  move <company> <stage>                 - Update stage (identified, contacted, etc.)

INFO
  summary                                - Daily stats
  help                                   - Show this help
  exit                                   - Quit

Examples:
  draft Spotify "Data Scientist" "Alex Johnson" alex@spotify.com
  add Meta "Software Engineer"
  move Meta contacted
  pipeline
"""
        self.print(help_text)
    
    async def handle_move(self, args):
        """Handle move command."""
        if len(args) < 2:
            self.print("❌ Usage: move <company> <stage>")
            self.print("   Stages: identified, researched, contacted, applied, interview, offer")
            return
        
        company = args[0]
        stage = args[1].lower()
        
        try:
            new_stage = PipelineStage(stage)
            # Find opportunity
            opps = [o for o in self.pipeline.get_active_opportunities() 
                   if o.company_name.lower() == company.lower()]
            if not opps:
                self.print(f"❌ No opportunity found for {company}")
                return
            
            updated = self.pipeline.advance_stage(opps[0].id, new_stage)
            self.print(f"✅ Moved {company} to {stage}")
        except ValueError:
            self.print(f"❌ Invalid stage: {stage}")
            self.print(f"   Valid: {', '.join([s.value for s in PipelineStage])}")
    
    async def run(self):
        """Main loop."""
        self.print_header()
        
        if not await self.initialize():
            return
        
        self.print("\nReady! Type 'help' for commands or 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                self.print("\n\nGoodbye! 👋")
                break
            
            if not user_input:
                continue
            
            # Use shlex to properly handle quoted strings
            parts = shlex.split(user_input)
            command = parts[0].lower()
            args = parts[1:]
            
            if command in ['exit', 'quit', 'bye']:
                self.print("Goodbye! 👋")
                break
            elif command == 'help':
                await self.handle_help()
            elif command == 'draft':
                await self.handle_draft(args)
            elif command == 'send':
                await self.handle_send(args)
            elif command == 'add':
                await self.handle_add(args)
            elif command == 'pipeline':
                await self.handle_pipeline(args)
            elif command == 'summary':
                await self.handle_summary(args)
            elif command == 'move':
                await self.handle_move(args)
            else:
                self.print(f"❓ Unknown command: {command}")
                self.print("   Type 'help' for available commands")


def main():
    """Entry point."""
    cli = SimpleMuBotCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()

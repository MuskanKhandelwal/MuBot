"""
MuBot Unified CLI Main Entry Point

Single entry point for all MuBot operations.
"""

import argparse
import asyncio
import importlib.util
import sys
from pathlib import Path


def load_commands_module():
    """Load commands module directly without going through mubot package."""
    cli_dir = Path(__file__).parent
    commands_path = cli_dir / "commands.py"
    spec = importlib.util.spec_from_file_location("cli_commands", commands_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="mubot",
        description="MuBot - Your Job Search Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive chat mode (default)
  python mubot.py
  
  # Natural language commands
  python mubot.py "send my follow-ups"
  python mubot.py "send 10 emails from my sheet"
  python mubot.py "check for replies"
  python mubot.py "show me status"
  python mubot.py "sync to sheets"
  
  # Structured subcommands
  python mubot.py campaign --limit 10
  python mubot.py followups --bulk
  python mubot.py list
  python mubot.py cancel "Company Name"
  
  # Daemon control
  python mubot.py --daemon start
  python mubot.py --daemon stop
  python mubot.py --daemon status
  python mubot.py --daemon command "send my follow-ups"
  
  # Chat modes
  python mubot.py --chat
  python mubot.py --chat-enhanced
        """
    )
    
    # Main modes
    parser.add_argument(
        "command",
        nargs="?",
        help="Natural language command or subcommand"
    )
    
    # Mode flags
    parser.add_argument(
        "--chat", "-c",
        action="store_true",
        help="Start interactive chat mode"
    )
    parser.add_argument(
        "--chat-enhanced", "-ce",
        action="store_true",
        help="Start enhanced interactive chat mode (with JD support)"
    )
    parser.add_argument(
        "--daemon", "-d",
        choices=["start", "stop", "status", "command"],
        help="Daemon control commands"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show status summary"
    )
    
    # Campaign options
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of items to process"
    )
    parser.add_argument(
        "--bulk", "-b",
        action="store_true",
        help="Bulk mode - no confirmations"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview mode - don't make changes"
    )
    
    # Company name for cancel/reschedule
    parser.add_argument(
        "--company",
        help="Company name for cancel/reschedule operations"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=3,
        help="Days for reschedule (default: 3)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force operation without confirmation"
    )
    
    # Daemon command text
    parser.add_argument(
        "--cmd-text",
        help="Command text for daemon command"
    )
    
    return parser


async def handle_natural_language(command: str, args) -> int:
    """Handle natural language command."""
    commands = load_commands_module()
    
    command_lower = command.lower().strip()
    
    # Send follow-ups
    if any(p in command_lower for p in ["follow-up", "followup"]):
        cmds = commands.FollowupCommands()
        await cmds.send_followups(
            dry_run=args.dry_run,
            bulk=args.bulk,
            limit=args.limit
        )
        return 0
    
    # Check replies
    if any(p in command_lower for p in ["reply", "response", "check email"]):
        cmds = commands.StatusCommands()
        await cmds.check_replies()
        return 0
    
    # Send emails/campaign
    if any(p in command_lower for p in ["send email", "send initial", "campaign", "send pending"]):
        cmds = commands.CampaignCommands()
        limit = args.limit or 10
        result = await cmds.send_emails(
            limit=limit,
            dry_run=args.dry_run,
            bulk=args.bulk
        )
        print(result.get("message", ""))
        return 0 if result.get("success") else 1
    
    # Cancel follow-ups
    if any(p in command_lower for p in ["cancel", "stop", "don't send"]):
        cmds = commands.FollowupCommands()
        # Try to extract company name
        company = args.company
        if not company:
            words = command.split()
            for i, word in enumerate(words):
                if word in ['for', 'at', 'to'] and i + 1 < len(words):
                    company = ' '.join(words[i+1:])
                    break
        if company:
            cmds.cancel_followups(company, force=args.force)
        else:
            print("❌ Please specify a company: 'cancel follow-ups for Company Name'")
            return 1
        return 0
    
    # Sync to sheets
    if any(p in command_lower for p in ["sync", "update sheet"]):
        cmds = commands.SyncCommands()
        await cmds.sync_sheets(dry_run=args.dry_run)
        return 0
    
    # Show status
    if any(p in command_lower for p in ["status", "summary", "what's up", "show me"]):
        cmds = commands.StatusCommands()
        result = await cmds.show_status()
        print(result.get("message", ""))
        return 0
    
    # List follow-ups
    if any(p in command_lower for p in ["list", "show follow-ups", "what's pending"]):
        cmds = commands.FollowupCommands()
        cmds.list_followups()
        return 0
    
    # Unknown command
    print(f"🤔 I don't understand: '{command}'")
    print("\nTry saying:")
    print('  • "send my follow-ups"')
    print('  • "send 10 emails from my sheet"')
    print('  • "check for replies"')
    print('  • "show me status"')
    print('  • "cancel follow-ups for Netflix"')
    print('  • "sync to sheets"')
    return 1


async def handle_subcommand(command: str, args) -> int:
    """Handle structured subcommand."""
    commands = load_commands_module()
    
    # Campaign subcommand
    if command == "campaign":
        cmds = commands.CampaignCommands()
        limit = args.limit or 50
        await cmds.run_campaign(
            limit=limit,
            dry_run=args.dry_run,
            bulk=args.bulk
        )
        return 0
    
    # Followups subcommand
    if command == "followups":
        cmds = commands.FollowupCommands()
        await cmds.send_followups(
            dry_run=args.dry_run,
            bulk=args.bulk,
            limit=args.limit
        )
        return 0
    
    # List subcommand
    if command == "list":
        cmds = commands.FollowupCommands()
        cmds.list_followups(show_all=args.dry_run)
        return 0
    
    # Cancel subcommand
    if command == "cancel":
        if not args.company:
            print("❌ Please specify a company with --company")
            return 1
        cmds = commands.FollowupCommands()
        cmds.cancel_followups(args.company, force=args.force)
        return 0
    
    # Mark-sent subcommand
    if command == "mark-sent":
        if not args.company:
            print("❌ Please specify a company with --company")
            return 1
        cmds = commands.FollowupCommands()
        cmds.mark_sent(args.company)
        return 0
    
    # Reschedule subcommand
    if command == "reschedule":
        if not args.company:
            print("❌ Please specify a company with --company")
            return 1
        cmds = commands.FollowupCommands()
        cmds.reschedule(args.company, args.days)
        return 0
    
    # Sync subcommand
    if command == "sync":
        cmds = commands.SyncCommands()
        await cmds.sync_sheets(dry_run=args.dry_run)
        return 0
    
    # Summary subcommand
    if command == "summary":
        cmds = commands.StatusCommands()
        await cmds.show_summary()
        return 0
    
    return 1


def load_daemon_module():
    """Load daemon control module directly."""
    cli_dir = Path(__file__).parent
    daemon_ctl_path = cli_dir / "daemon_ctl.py"
    spec = importlib.util.spec_from_file_location("daemon_ctl", daemon_ctl_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_interactive_module():
    """Load interactive module directly."""
    cli_dir = Path(__file__).parent
    interactive_path = cli_dir / "interactive.py"
    spec = importlib.util.spec_from_file_location("interactive", interactive_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def main_async() -> int:
    """Main async entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle daemon mode
    if args.daemon:
        daemon_module = load_daemon_module()
        controller = daemon_module.DaemonController()
        
        if args.daemon == "start":
            return controller.start()
        elif args.daemon == "stop":
            return controller.stop()
        elif args.daemon == "status":
            return controller.status()
        elif args.daemon == "command":
            command_text = args.cmd_text or input("Enter command: ")
            result = controller.send_command(command_text)
            print(f"\n📥 Response:\n{result.get('message', 'No response')}")
            return 0
    
    # Handle chat modes
    if args.chat:
        interactive_module = load_interactive_module()
        return await interactive_module.run_interactive(enhanced=False)
    
    if args.chat_enhanced:
        interactive_module = load_interactive_module()
        return await interactive_module.run_interactive(enhanced=True)
    
    # Handle status flag
    if args.status:
        commands = load_commands_module()
        cmds = commands.StatusCommands()
        result = await cmds.show_status()
        print(result.get("message", ""))
        return 0
    
    # Handle natural language or subcommand
    if args.command:
        # Check if it's a subcommand
        subcommands = ["campaign", "followups", "list", "cancel", "mark-sent", "reschedule", "sync", "summary"]
        if args.command in subcommands:
            return await handle_subcommand(args.command, args)
        else:
            return await handle_natural_language(args.command, args)
    
    # Default: interactive mode
    interactive_module = load_interactive_module()
    return await interactive_module.run_interactive(enhanced=True)


def main() -> int:
    """Main entry point."""
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        return 0


# Keep 'cli' alias for backward compatibility
cli = main


if __name__ == "__main__":
    sys.exit(main())

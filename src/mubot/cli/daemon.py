"""
MuBot Daemon

Background daemon that handles scheduled tasks and automated operations.
Extracted from mubot_daemon.py.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mubot.agent import JobSearchAgent
from integrations.google_sheets import GoogleSheetsIntegration

PID_FILE = Path("data/mubot.pid")
LOG_FILE = Path("logs/mubot_daemon.log")
COMMAND_FILE = Path("data/mubot_command.json")
STATUS_FILE = Path("data/mubot_status.json")
RESULT_FILE = Path("data/mubot_result.json")


class Daemon:
    """Background daemon for MuBot."""
    
    def __init__(self):
        self.running = False
        self.agent: Optional[JobSearchAgent] = None
        self.sheets: Optional[GoogleSheetsIntegration] = None
        self.last_check = None
        self.status = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "emails_sent": 0,
            "followups_sent": 0,
            "replies_received": 0,
            "last_activity": None,
            "scheduled_jobs": []
        }
        
    def _load_status(self):
        """Load persistent status."""
        if STATUS_FILE.exists():
            with open(STATUS_FILE) as f:
                loaded = json.load(f)
                self.status.update(loaded)
    
    def _save_status(self):
        """Save persistent status."""
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_FILE, 'w') as f:
            json.dump(self.status, f, indent=2)
    
    def _log(self, message: str):
        """Log to file and print."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        print(log_entry)
        
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry + "\n")
    
    async def initialize(self):
        """Initialize connections."""
        self._log("🤖 Initializing MuBot Daemon...")
        
        self.agent = JobSearchAgent()
        await self.agent.initialize()
        
        self.sheets = GoogleSheetsIntegration(
            credentials_path="./credentials/sheets_credentials.json",
            spreadsheet_name="Job Applications"
        )
        
        self._load_status()
        self._log("✅ MuBot ready")
    
    def run(self) -> int:
        """Run the daemon."""
        self._save_pid()
        self._log("🚀 MuBot Daemon started")
        self._log(f"   PID: {os.getpid()}")
        self._log(f"   Log: {LOG_FILE}")
        
        try:
            asyncio.run(self._run_async())
        except KeyboardInterrupt:
            pass
        finally:
            self._log("🛑 MuBot Daemon stopped")
            self._remove_pid()
        
        return 0
    
    async def _run_async(self):
        """Async main loop."""
        await self.initialize()
        
        self.running = True
        
        # Schedule background tasks
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._command_listener())
        
        # Main loop
        while self.running:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
    
    def _save_pid(self):
        """Save process ID."""
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    
    def _remove_pid(self):
        """Remove PID file."""
        if PID_FILE.exists():
            PID_FILE.unlink()
    
    async def _heartbeat_loop(self):
        """Periodic background tasks."""
        while self.running:
            try:
                now = datetime.now(timezone.utc)
                
                # Check for scheduled follow-ups every hour
                if self.last_check is None or (now - self.last_check).seconds > 3600:
                    self._log("💓 Heartbeat: Checking for tasks...")
                    await self._auto_check_followups()
                    self.last_check = now
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self._log(f"❌ Heartbeat error: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    
    async def _auto_check_followups(self):
        """Automatically check and report on follow-ups."""
        state = self.agent.memory.load_heartbeat_state()
        now = datetime.now(timezone.utc)
        
        due = []
        for task in state.scheduled_followups:
            if not task.get('sent'):
                due_at_str = task.get('due_at', '')
                try:
                    if due_at_str.endswith('Z'):
                        due_at = datetime.fromisoformat(due_at_str.replace('Z', '+00:00'))
                    elif '+' in due_at_str or '-' in due_at_str[-6:]:
                        due_at = datetime.fromisoformat(due_at_str)
                    else:
                        due_at = datetime.fromisoformat(due_at_str).replace(tzinfo=timezone.utc)
                    if due_at <= now:
                        due.append(task)
                except (ValueError, TypeError):
                    continue
        
        if due:
            self._log(f"📧 {len(due)} follow-ups are due")
            # Could auto-send here if configured
            self._notify_user(f"📧 {len(due)} follow-ups are ready to send")
    
    async def _command_listener(self):
        """Listen for commands from CLI."""
        while self.running:
            try:
                if COMMAND_FILE.exists():
                    with open(COMMAND_FILE) as f:
                        cmd_data = json.load(f)
                    
                    # Process command
                    command = cmd_data.get('command', '')
                    self._log(f"📨 Received command: {command}")
                    
                    result = await self._process_command(command)
                    
                    # Save result
                    cmd_data['result'] = result
                    cmd_data['processed_at'] = datetime.now(timezone.utc).isoformat()
                    
                    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
                    with open(RESULT_FILE, 'w') as f:
                        json.dump(cmd_data, f, indent=2)
                    
                    # Remove command file to prevent reprocessing
                    COMMAND_FILE.unlink()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self._log(f"❌ Command error: {e}")
                await asyncio.sleep(5)
    
    async def _process_command(self, command: str) -> dict:
        """Process natural language command."""
        from mubot.cli.commands import (
            CampaignCommands,
            FollowupCommands,
            StatusCommands,
            SyncCommands,
        )
        
        command = command.lower().strip()
        result = {"success": False, "message": "Unknown command"}
        
        # Command: Send follow-ups
        if any(phrase in command for phrase in ["send follow-up", "send followup", "send my follow-ups", "send my followups"]):
            self._log("🚀 Executing: Send follow-ups")
            cmds = FollowupCommands(agent=self.agent, sheets=self.sheets)
            await cmds.send_followups(bulk=True)  # Daemon runs in bulk mode
            result = {"success": True, "message": "Follow-ups sent"}
        
        # Command: Check replies
        elif any(phrase in command for phrase in ["check reply", "check for replies", "any replies", "new responses"]):
            self._log("🚀 Executing: Check replies")
            cmds = StatusCommands(agent=self.agent, sheets=self.sheets)
            result = await cmds.check_replies()
        
        # Command: Send initial emails
        elif any(phrase in command for phrase in ["send emails", "send initial", "campaign", "send pending"]):
            self._log("🚀 Executing: Send emails")
            cmds = CampaignCommands(agent=self.agent, sheets=self.sheets)
            result = await cmds.send_emails(bulk=True)  # Daemon runs in bulk mode
        
        # Command: Get status
        elif any(phrase in command for phrase in ["status", "summary", "what's happening", "show me"]):
            self._log("🚀 Executing: Status check")
            cmds = StatusCommands(agent=self.agent, sheets=self.sheets)
            result = await cmds.show_status()
        
        # Command: Sync to sheets
        elif any(phrase in command for phrase in ["sync", "update sheet"]):
            self._log("🚀 Executing: Sync to Google Sheets")
            cmds = SyncCommands(agent=self.agent, sheets=self.sheets)
            result = await cmds.sync_sheets()
        
        else:
            result = {
                "success": False,
                "message": f"I don't understand: '{command}'\n\nTry:\n• 'send my follow-ups'\n• 'check for replies'\n• 'show me status'"
            }
        
        return result
    
    def _notify_user(self, message: str):
        """Send notification to user."""
        self._log(f"🔔 NOTIFICATION: {message}")
        # TODO: Add desktop notifications, email summaries, etc.

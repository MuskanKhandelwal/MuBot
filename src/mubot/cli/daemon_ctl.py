"""
MuBot Daemon Control

Provides daemon control functionality extracted from mubot_daemon.py.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# PID and status files
PID_FILE = Path("data/mubot.pid")
LOG_FILE = Path("logs/mubot_daemon.log")
COMMAND_FILE = Path("data/mubot_command.json")
STATUS_FILE = Path("data/mubot_status.json")


class DaemonController:
    """Controller for MuBot daemon operations."""
    
    def start(self):
        """Start the daemon process."""
        if PID_FILE.exists():
            with open(PID_FILE) as f:
                old_pid = f.read().strip()
            if Path(f"/proc/{old_pid}").exists():
                print(f"❌ Daemon already running (PID: {old_pid})")
                return 1
            else:
                PID_FILE.unlink()
        
        print("🚀 Starting MuBot Daemon...")
        
        # Fork process (Unix-like) or use subprocess
        if hasattr(os, 'fork'):
            pid = os.fork()
            if pid > 0:
                print(f"✅ Daemon started (PID: {pid})")
                print(f"   Log: {LOG_FILE}")
                return 0
        else:
            # Windows/Mac - use subprocess
            subprocess.Popen(
                [sys.executable, "-m", "mubot.cli.daemon_ctl", "--internal-run"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
            )
            print("✅ Daemon started")
            return 0
        
        # Child process - run daemon
        from mubot.cli.daemon import Daemon
        daemon = Daemon()
        return daemon.run()
    
    def stop(self):
        """Stop the daemon process."""
        if not PID_FILE.exists():
            print("❌ Daemon not running")
            return 1
        
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"✅ Stopped daemon (PID: {pid})")
            return 0
        except ProcessLookupError:
            print("⚠️  Process not found, cleaning up")
            PID_FILE.unlink()
            return 1
    
    def status(self):
        """Check daemon status."""
        if PID_FILE.exists():
            with open(PID_FILE) as f:
                pid = f.read().strip()
            
            # Check if process exists
            if Path(f"/proc/{pid}").exists():
                print(f"✅ MuBot Daemon is running (PID: {pid})")
                
                if STATUS_FILE.exists():
                    with open(STATUS_FILE) as f:
                        status = json.load(f)
                    print(f"\n📊 Activity:")
                    print(f"   Emails sent: {status.get('emails_sent', 0)}")
                    print(f"   Follow-ups sent: {status.get('followups_sent', 0)}")
                    print(f"   Replies: {status.get('replies_received', 0)}")
                    print(f"   Started: {status.get('started_at', 'unknown')[:10]}")
                
                return 0
            else:
                print("⚠️  Stale PID file found, cleaning up")
                PID_FILE.unlink()
        
        print("❌ MuBot Daemon is not running")
        print("   Start with: python mubot.py --daemon start")
        return 1
    
    def send_command(self, command: str) -> dict:
        """Send command to running daemon and wait for response."""
        if not PID_FILE.exists():
            print("❌ MuBot daemon is not running")
            print("   Start it with: python mubot.py --daemon start")
            return {"error": "Daemon not running"}
        
        # Write command file
        COMMAND_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(COMMAND_FILE, 'w') as f:
            json.dump({
                "command": command,
                "sent_at": datetime.now(timezone.utc).isoformat()
            }, f)
        
        print(f"📤 Sending command: '{command}'")
        print("⏳ Waiting for response...")
        
        # Wait for response (with timeout)
        for i in range(60):  # 60 second timeout
            time.sleep(1)
            
            if not COMMAND_FILE.exists():
                # Command processed
                break
        
        # Read result
        result_file = Path("data/mubot_result.json")
        if result_file.exists():
            with open(result_file) as f:
                return json.load(f)
        
        return {"message": "Command sent (check logs for result)"}


def main():
    """Main entry point for daemon control."""
    parser = argparse.ArgumentParser(description="MuBot Daemon Control")
    parser.add_argument(
        "action",
        choices=["start", "stop", "status", "command", "--internal-run"],
        help="Action to perform"
    )
    parser.add_argument(
        "command_text",
        nargs="?",
        help="Command to send (for 'command' action)"
    )
    
    args = parser.parse_args()
    
    controller = DaemonController()
    
    if args.action == "start":
        return controller.start()
    elif args.action == "stop":
        return controller.stop()
    elif args.action == "status":
        return controller.status()
    elif args.action == "command":
        if not args.command_text:
            print("❌ Please provide a command")
            print("   Example: python mubot.py --daemon command 'send my follow-ups'")
            return 1
        result = controller.send_command(args.command_text)
        print(f"\n📥 Response:\n{result.get('message', 'No response')}")
        return 0
    elif args.action == "--internal-run":
        from mubot.cli.daemon import Daemon
        daemon = Daemon()
        return daemon.run()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

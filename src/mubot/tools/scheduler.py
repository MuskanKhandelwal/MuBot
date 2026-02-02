"""
Scheduler Module

This module provides task scheduling and heartbeat functionality for MuBot.
It manages:
- Delayed email sending
- Follow-up reminders
- Periodic inbox checking
- Daily summary generation

The scheduler uses APScheduler for robust task management and
can be run as a background process or invoked manually.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from mubot.config.settings import Settings
from mubot.memory import MemoryManager


class ScheduledTask:
    """Represents a scheduled task."""
    
    def __init__(
        self,
        task_id: str,
        task_type: str,
        scheduled_time: datetime,
        data: dict,
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.scheduled_time = scheduled_time
        self.data = data
        self.executed = False
        self.executed_at: Optional[datetime] = None


class Scheduler:
    """
    Task scheduler and heartbeat manager.
    
    The Scheduler handles all time-based operations in MuBot:
    - Scheduling emails for future delivery
    - Setting follow-up reminders
    - Running periodic heartbeat checks
    - Generating daily summaries
    
    Usage:
        scheduler = Scheduler(settings, memory, agent)
        await scheduler.start()
        
        # Schedule an email
        scheduler.schedule_email(
            entry=draft,
            send_at=datetime.now() + timedelta(hours=2),
        )
        
        # Schedule daily heartbeat
        scheduler.schedule_daily_heartbeat(hour=9, minute=0)
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        memory: Optional[MemoryManager] = None,
        agent=None,
    ):
        """
        Initialize the scheduler.
        
        Args:
            settings: Application settings
            memory: MemoryManager for persistence
            agent: JobSearchAgent for executing tasks
        """
        self.settings = settings or Settings()
        self.memory = memory
        self.agent = agent
        
        # APScheduler instance
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
        
        # Task storage
        self._tasks: dict[str, ScheduledTask] = {}
    
    async def start(self) -> bool:
        """
        Start the scheduler.
        
        Returns:
            True if started successfully
        """
        if self._running:
            return True
        
        try:
            # Create event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Initialize scheduler
            self._scheduler = AsyncIOScheduler(event_loop=loop)
            
            # Configure timezone
            if self.settings.scheduler_timezone:
                self._scheduler.configure(timezone=self.settings.scheduler_timezone)
            
            self._scheduler.start()
            self._running = True
            
            print("✓ Scheduler started")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start scheduler: {e}")
            return False
    
    async def stop(self):
        """Stop the scheduler."""
        if self._scheduler:
            self._scheduler.shutdown()
            self._running = False
            print("✓ Scheduler stopped")
    
    # ======================================================================
    # Task Scheduling Methods
    # ======================================================================
    
    def schedule_email(
        self,
        entry,
        send_at: datetime,
    ) -> Optional[str]:
        """
        Schedule an email for future delivery.
        
        Args:
            entry: OutreachEntry to send
            send_at: When to send the email
        
        Returns:
            Task ID if scheduled successfully
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler not started")
        
        task_id = f"email_{entry.id}"
        
        # Create scheduled task record
        task = ScheduledTask(
            task_id=task_id,
            task_type="send_email",
            scheduled_time=send_at,
            data={"entry_id": entry.id},
        )
        self._tasks[task_id] = task
        
        # Schedule with APScheduler
        self._scheduler.add_job(
            func=self._execute_email_send,
            trigger=DateTrigger(run_date=send_at),
            id=task_id,
            args=[entry],
            replace_existing=True,
        )
        
        # Update entry in memory
        entry.status = "scheduled"
        if self.memory:
            self.memory.save_outreach_entry(entry)
        
        return task_id
    
    def schedule_followup(
        self,
        entry,
        days_delay: Optional[int] = None,
    ) -> Optional[str]:
        """
        Schedule a follow-up email.
        
        Args:
            entry: Original outreach entry
            days_delay: Days to wait (default: from settings)
        
        Returns:
            Task ID if scheduled successfully
        """
        days_delay = days_delay or self.settings.default_followup_delay_days
        send_at = datetime.utcnow() + timedelta(days=days_delay)
        
        task_id = f"followup_{entry.id}"
        
        task = ScheduledTask(
            task_id=task_id,
            task_type="followup",
            scheduled_time=send_at,
            data={
                "entry_id": entry.id,
                "company": entry.company_name,
                "followup_number": entry.followup_count + 1,
            },
        )
        self._tasks[task_id] = task
        
        self._scheduler.add_job(
            func=self._execute_followup,
            trigger=DateTrigger(run_date=send_at),
            id=task_id,
            args=[entry],
            replace_existing=True,
        )
        
        return task_id
    
    def schedule_daily_heartbeat(
        self,
        hour: int = 9,
        minute: int = 0,
    ) -> Optional[str]:
        """
        Schedule the daily heartbeat check.
        
        The heartbeat runs at a specified time each day to:
        - Check for replies
        - Send pending follow-ups
        - Generate daily summary
        
        Args:
            hour: Hour to run (24-hour format)
            minute: Minute to run
        
        Returns:
            Job ID if scheduled successfully
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler not started")
        
        job_id = "daily_heartbeat"
        
        self._scheduler.add_job(
            func=self._execute_heartbeat,
            trigger=CronTrigger(hour=hour, minute=minute),
            id=job_id,
            replace_existing=True,
        )
        
        print(f"✓ Daily heartbeat scheduled for {hour:02d}:{minute:02d}")
        return job_id
    
    def schedule_inbox_check(
        self,
        interval_minutes: int = 60,
    ) -> Optional[str]:
        """
        Schedule periodic inbox checking.
        
        Args:
            interval_minutes: How often to check (default: 60)
        
        Returns:
            Job ID if scheduled successfully
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler not started")
        
        job_id = "inbox_check"
        
        self._scheduler.add_job(
            func=self._execute_inbox_check,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            replace_existing=True,
        )
        
        print(f"✓ Inbox check scheduled every {interval_minutes} minutes")
        return job_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: ID of task to cancel
        
        Returns:
            True if cancelled successfully
        """
        try:
            self._scheduler.remove_job(task_id)
            if task_id in self._tasks:
                del self._tasks[task_id]
            return True
        except Exception:
            return False
    
    def get_pending_tasks(self) -> list[ScheduledTask]:
        """
        Get all pending (non-executed) tasks.
        
        Returns:
            List of pending tasks
        """
        return [t for t in self._tasks.values() if not t.executed]
    
    # ======================================================================
    # Task Execution Methods
    # ======================================================================
    
    async def _execute_email_send(self, entry):
        """Execute a scheduled email send."""
        print(f"Executing scheduled email send to {entry.recipient_email}")
        
        if self.agent:
            success, message = await self.agent.send_email(entry, approved=True)
            print(f"Result: {message}")
        
        # Mark task as executed
        task_id = f"email_{entry.id}"
        if task_id in self._tasks:
            self._tasks[task_id].executed = True
            self._tasks[task_id].executed_at = datetime.utcnow()
    
    async def _execute_followup(self, entry):
        """Execute a scheduled follow-up."""
        print(f"Executing follow-up for {entry.company_name}")
        
        # Check if we already got a reply
        if entry.status.value == "replied":
            print("Already received reply, skipping follow-up")
            return
        
        if self.agent:
            # Generate follow-up content
            followup_body = await self.agent.reasoning.draft_followup(
                entry,
                days_elapsed=self.settings.default_followup_delay_days,
            )
            
            # TODO: Actually send the follow-up
            print(f"Follow-up draft generated: {followup_body[:200]}...")
    
    async def _execute_heartbeat(self):
        """Execute the daily heartbeat."""
        print("=" * 60)
        print("💓 Running daily heartbeat")
        print("=" * 60)
        
        # Update heartbeat state
        if self.memory:
            state = self.memory.load_heartbeat_state()
            state.last_run = datetime.utcnow()
            self.memory.save_heartbeat_state(state)
        
        # Check for pending follow-ups
        if self.memory:
            pending = self.memory.get_pending_followups()
            print(f"📬 {len(pending)} follow-ups due")
        
        # Check for replies
        await self._execute_inbox_check()
        
        # Generate daily summary
        if self.agent:
            summary = await self.agent.get_daily_summary()
            print("\n" + summary)
        
        print("=" * 60)
        print("💓 Heartbeat complete")
        print("=" * 60)
    
    async def _execute_inbox_check(self):
        """Execute inbox check for replies."""
        print("📥 Checking inbox for replies...")
        
        # TODO: Implement actual inbox checking via Gmail API
        # For now, placeholder
        print("✓ Inbox check complete")
    
    # ======================================================================
    # Manual Execution
    # ======================================================================
    
    async def run_heartbeat_now(self):
        """Run heartbeat immediately (for manual execution)."""
        await self._execute_heartbeat()

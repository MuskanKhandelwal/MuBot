"""
Memory Manager

The MemoryManager is the central interface for all memory operations in MuBot.
It coordinates between:
- Short-term memory (current session context)
- Working memory (active drafts and temporary data)
- Long-term memory (file-backed persistence via FileStore and JsonStore)

This class provides high-level methods for common operations while
abstracting the underlying storage details.

Key Responsibilities:
1. Load and parse USER.md, MEMORY.md, TOOLS.md
2. Track daily outreach activity
3. Manage outreach entries and their lifecycle
4. Query historical data for context
5. Update memory based on outcomes
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from mubot.memory.models import (
    CompanyHistory,
    DailyStats,
    EmailThread,
    HeartbeatState,
    OutreachEntry,
    OutreachStatus,
    ResponseCategory,
    UserProfile,
)
from mubot.memory.persistence import FileStore, JsonStore, MemoryInitializer


class MemoryManager:
    """
    Central coordinator for all memory operations.
    
    This class follows the Singleton pattern (one instance per base_path)
    to ensure consistency across the application.
    
    Usage:
        from memory import MemoryManager
        
        memory = MemoryManager("./data")
        user = memory.load_user_profile()
        memory.log_outreach(entry)
    """
    
    def __init__(self, base_path: str | Path):
        """
        Initialize the memory manager.
        
        Args:
            base_path: Root directory for all memory files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage backends
        self.file_store = FileStore(self.base_path)
        self.json_store = JsonStore(self.base_path)
        
        # Initialize default files if they don't exist
        self._initializer = MemoryInitializer(self.base_path)
        self._initializer.initialize()
        
        # Cache for frequently accessed data
        self._user_profile: Optional[UserProfile] = None
        self._heartbeat_state: Optional[HeartbeatState] = None
    
    # ======================================================================
    # User Profile Operations
    # ======================================================================
    
    def load_user_profile(self) -> Optional[UserProfile]:
        """
        Load and parse the USER.md file into a UserProfile object.
        
        This is typically called at the start of each session to
        personalize the agent's behavior.
        
        Returns:
            UserProfile if valid USER.md exists, None otherwise
        """
        if self._user_profile is not None:
            return self._user_profile
        
        result = self.file_store.read_markdown("USER.md")
        if result is None:
            return None
        
        metadata, content = result
        
        # Parse the markdown content to extract user information
        # This is a simplified parser - in production, you might want
        # more sophisticated markdown parsing
        try:
            profile_data = self._parse_user_md(content)
            profile_data.update(metadata)
            self._user_profile = UserProfile.model_validate(profile_data)
            return self._user_profile
        except Exception as e:
            print(f"Error parsing USER.md: {e}")
            return None
    
    def _parse_user_md(self, content: str) -> dict:
        """
        Parse USER.md markdown content into a dictionary.
        
        This is a simple parser that looks for specific sections.
        """
        data = {}
        lines = content.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Section headers
            if line.startswith("## "):
                current_section = line[3:].lower().replace(" ", "_")
            
            # Identity fields
            elif "**Name**:" in line:
                data["name"] = line.split(":", 1)[1].strip(" []")
            elif "**Email**:" in line:
                data["email"] = line.split(":", 1)[1].strip(" []")
            elif "**Phone**:" in line:
                phone = line.split(":", 1)[1].strip(" []")
                if phone and phone != "[optional]":
                    data["phone"] = phone
            elif "**Timezone**:" in line:
                data["timezone"] = line.split(":", 1)[1].strip()
            
            # Preferences
            elif "**Email Tone**:" in line:
                tone = line.split(":", 1)[1].strip().lower()
                if tone in ["formal", "friendly", "bold"]:
                    data["preferred_tone"] = tone
            
            # Professional info
            elif "**Current Title**:" in line:
                data["current_title"] = line.split(":", 1)[1].strip()
            elif "**Years of Experience**:" in line:
                try:
                    data["years_experience"] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif "**Summary**:" in line:
                data["summary"] = line.split(":", 1)[1].strip()
            elif "**Resume**:" in line or "**Resume Path**:" in line:
                path_str = line.split(":", 1)[1].strip()
                if path_str and path_str != "[optional]":
                    from pathlib import Path
                    data["resume_path"] = Path(path_str)
            
            # Links
            elif "**LinkedIn**:" in line:
                url = line.split(":", 1)[1].strip()
                if url and not url.startswith("["):
                    data["linkedin_url"] = url
            elif "**GitHub**:" in line:
                url = line.split(":", 1)[1].strip()
                if url and not url.startswith("["):
                    data["github_url"] = url
        
        return data
    
    # ======================================================================
    # Outreach Entry Operations
    # ======================================================================
    
    def save_outreach_entry(self, entry: OutreachEntry) -> bool:
        """
        Save an outreach entry to today's memory log.
        
        Entries are stored in memory/YYYY-MM-DD.md files with full
        context for later retrieval and analysis.
        
        Args:
            entry: The outreach entry to save
        
        Returns:
            True if saved successfully
        """
        date_str = entry.created_at.strftime("%Y-%m-%d")
        file_path = f"memory/{date_str}.md"
        
        # Format the entry as markdown
        entry_md = self._format_outreach_entry(entry)
        
        # Append to daily log
        return self.file_store.append_to_markdown(file_path, entry_md)
    
    def _format_outreach_entry(self, entry: OutreachEntry) -> str:
        """Format an outreach entry as markdown for storage."""
        return f"""## Outreach: {entry.company_name} - {entry.role_title}

**ID**: {entry.id}
**Status**: {entry.status.value}
**Created**: {entry.created_at.isoformat()}

### Recipient
- **Name**: {entry.recipient_name or "Unknown"}
- **Email**: {entry.recipient_email}
- **Title**: {entry.recipient_title or "Unknown"}

### Email Content
**Subject**: {entry.subject}

**Body**:
{entry.body}

### Personalization
{chr(10).join(f"- {p}" for p in entry.personalization_elements) or "- None"}

### Timeline
- Drafted: {entry.drafted_at.isoformat() if entry.drafted_at else "N/A"}
- Sent: {entry.sent_at.isoformat() if entry.sent_at else "N/A"}
- Replied: {entry.replied_at.isoformat() if entry.replied_at else "N/A"}

### Follow-ups
- Count: {entry.followup_count}/{entry.max_followups}
- Next scheduled: {entry.next_followup_scheduled.isoformat() if entry.next_followup_scheduled else "None"}

### Response
**Category**: {entry.response_category.value if entry.response_category else "N/A"}
**Body**: {entry.response_body or "N/A"}

---
"""
    
    def get_company_history(self, company_name: str) -> CompanyHistory:
        """
        Retrieve or create history for a specific company.
        
        This aggregates all outreach to a company to prevent duplicate
        contacts and inform personalization.
        
        Args:
            company_name: Company name to look up
        
        Returns:
            CompanyHistory object (creates new if not exists)
        """
        # Search through memory files for entries with this company
        # This is a simplified implementation - in production, you might
        # want to maintain an index for faster lookups
        history = CompanyHistory(company_name=company_name)
        
        # TODO: Implement search through memory files
        # For now, return empty history
        return history
    
    # ======================================================================
    # Daily Stats Operations
    # ======================================================================
    
    def get_daily_stats(self, date: Optional[datetime] = None) -> DailyStats:
        """
        Get statistics for a specific day.
        
        Args:
            date: Date to get stats for (default: today)
        
        Returns:
            DailyStats object with counts
        """
        if date is None:
            date = datetime.utcnow()
        
        date_str = date.strftime("%Y-%m-%d")
        
        # Try to load from memory file
        result = self.file_store.read_markdown(f"memory/{date_str}.md")
        
        if result is None:
            return DailyStats(date=date_str)
        
        # Parse the markdown to count entries
        metadata, content = result
        
        stats = DailyStats(date=date_str)
        
        # Count outreach entries in the content
        stats.emails_sent = content.count("Status: sent")
        stats.replies_received = content.count("Status: replied")
        stats.positive_responses = content.count("Category: positive")
        stats.rejections = content.count("Category: rejection")
        
        return stats
    
    
    # ======================================================================
    # Heartbeat State Operations
    # ======================================================================
    
    def load_heartbeat_state(self) -> HeartbeatState:
        """
        Load the current heartbeat state.
        
        The heartbeat state tracks scheduled tasks, follow-ups,
        and rate limiting information.
        
        Returns:
            Current HeartbeatState (creates new if not exists)
        """
        if self._heartbeat_state is not None:
            return self._heartbeat_state
        
        state = self.json_store.read_pydantic("heartbeat-state.json", HeartbeatState)
        
        if state is None:
            state = HeartbeatState()
            self.json_store.write_pydantic("heartbeat-state.json", state)
        
        self._heartbeat_state = state
        return state
    
    def save_heartbeat_state(self, state: HeartbeatState) -> bool:
        """
        Save the heartbeat state to disk.
        
        Args:
            state: HeartbeatState to save
        
        Returns:
            True if saved successfully
        """
        self._heartbeat_state = state
        return self.json_store.write_pydantic("heartbeat-state.json", state)
    
    # ======================================================================
    # Query Operations
    # ======================================================================
    
    def search_outreach(
        self,
        company: Optional[str] = None,
        status: Optional[OutreachStatus] = None,
        days: int = 30
    ) -> list[OutreachEntry]:
        """
        Search for outreach entries matching criteria.
        
        Args:
            company: Filter by company name
            status: Filter by outreach status
            days: Look back this many days
        
        Returns:
            List of matching OutreachEntry objects
        """
        # TODO: Implement search across memory files
        # This would involve:
        # 1. Finding all memory/YYYY-MM-DD.md files in the date range
        # 2. Parsing each file
        # 3. Filtering by criteria
        return []
    
    def get_pending_followups(self) -> list[dict]:
        """
        Get all scheduled follow-ups that are due.
        
        Returns:
            List of follow-up tasks with context
        """
        state = self.load_heartbeat_state()
        now = datetime.utcnow()
        
        pending = []
        for task in state.scheduled_followups:
            due_time = datetime.fromisoformat(task.get("due_at", ""))
            if due_time <= now:
                pending.append(task)
        
        return pending
    
    # ======================================================================
    # Memory Update Operations
    # ======================================================================
    
    def update_memory_md(self, section: str, content: str) -> bool:
        """
        Update a section in MEMORY.md.
        
        Args:
            section: Section name (e.g., "What's Working")
            content: New content for the section
        
        Returns:
            True if updated successfully
        """
        result = self.file_store.read_markdown("MEMORY.md")
        if result is None:
            return False
        
        metadata, existing_content = result
        
        # Update the timestamp
        metadata["last_updated"] = datetime.utcnow().isoformat()
        
        # TODO: Implement section replacement logic
        # For now, just append
        new_content = existing_content + f"\n\n## {section} (Updated)\n{content}"
        
        return self.file_store.write_markdown("MEMORY.md", metadata, new_content)
    
    def log_learning(self, what_worked: str, context: str) -> bool:
        """
        Log a learning to MEMORY.md for future reference.
        
        Args:
            what_worked: Description of what worked
            context: Additional context (company, role, etc.)
        
        Returns:
            True if logged successfully
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d")
        entry = f"- [{timestamp}] {what_worked} (Context: {context})"
        
        return self.update_memory_md("What's Working", entry)

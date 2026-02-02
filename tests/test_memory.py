"""
Memory System Tests

Tests for the memory management functionality.
"""

import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from mubot.memory import MemoryManager
from memory.models import OutreachEntry, OutreachStatus


class TestMemoryManager:
    """Tests for MemoryManager class."""
    
    @pytest.fixture
    def temp_memory(self):
        """Create a temporary memory directory."""
        with TemporaryDirectory() as tmpdir:
            yield MemoryManager(tmpdir)
    
    def test_initialization_creates_files(self, temp_memory):
        """Test that initialization creates required files."""
        base = Path(temp_memory.base_path)
        
        assert (base / "USER.md").exists()
        assert (base / "MEMORY.md").exists()
        assert (base / "TOOLS.md").exists()
        assert (base / "heartbeat-state.json").exists()
    
    def test_save_and_retrieve_outreach(self, temp_memory):
        """Test saving and retrieving outreach entries."""
        entry = OutreachEntry(
            id="test-123",
            recipient_email="test@example.com",
            company_name="Test Corp",
            role_title="Engineer",
            subject="Test Subject",
            body="Test body",
            status=OutreachStatus.DRAFT,
        )
        
        result = temp_memory.save_outreach_entry(entry)
        assert result is True
        
        # Check daily log file was created
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = Path(temp_memory.base_path) / "memory" / f"{date_str}.md"
        assert log_file.exists()
        
        content = log_file.read_text()
        assert "Test Corp" in content
        assert "Engineer" in content
    
    def test_daily_stats_empty(self, temp_memory):
        """Test daily stats when no activity."""
        stats = temp_memory.get_daily_stats()
        
        assert stats.emails_sent == 0
        assert stats.replies_received == 0
        assert not stats.limit_reached

# =============================================================================
# Memory Package
# =============================================================================
# The memory system is the foundation of MuBot's long-term persistence.
# Unlike stateless AI systems, MuBot uses file-based memory to:
#   - Remember user preferences across sessions
#   - Track outreach history and outcomes
#   - Learn from past interactions
#   - Maintain continuity in job search campaigns
#
# Architecture:
#   - Short-term: Current chat context (handled by LLM)
#   - Working: Active drafts and temporary notes (in-memory)
#   - Long-term: File-backed storage (persistent)
#
# This package provides a clean interface for reading, writing, and querying
# memory across all time horizons.
# =============================================================================

from mubot.memory.manager import MemoryManager
from mubot.memory.models import (
    MemoryEntry,
    OutreachEntry,
    CompanyHistory,
    UserProfile,
    EmailThread,
)
from mubot.memory.persistence import FileStore, JsonStore

__all__ = [
    "MemoryManager",
    "MemoryEntry",
    "OutreachEntry",
    "CompanyHistory",
    "UserProfile",
    "EmailThread",
    "FileStore",
    "JsonStore",
]

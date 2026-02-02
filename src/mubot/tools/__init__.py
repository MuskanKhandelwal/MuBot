# =============================================================================
# Tools Package
# =============================================================================
# This package implements the tool layer of MuBot's architecture.
# Tools provide the actual capabilities that the agent uses to interact
# with external systems like Gmail, vector stores, and scheduling services.
#
# Design Philosophy:
#   - Each tool is self-contained and testable
#   - Tools follow a consistent interface pattern
#   - Error handling is explicit and informative
#   - Async operations are preferred for I/O bound tasks
#
# Available Tools:
#   - GmailClient: Send, receive, and organize emails
#   - RAGEngine: Semantic search over past outreach
#   - Scheduler: Delayed execution and heartbeat management
# =============================================================================

from mubot.tools.gmail_client import GmailClient
from mubot.tools.rag_engine import RAGEngine
from mubot.tools.scheduler import Scheduler

__all__ = [
    "GmailClient",
    "RAGEngine",
    "Scheduler",
]

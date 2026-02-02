"""
MuBot - Job Search Cold Emailing Agent

Your AI-powered job search copilot for crafting personalized cold emails,
tracking applications, and managing follow-ups.
"""

__version__ = "0.1.0"

# Main exports
from mubot.agent import JobSearchAgent
from mubot.agent.safety import SafetyGuardrails
from mubot.agent.nlp_interface import NLExecutor

__all__ = [
    "JobSearchAgent",
    "SafetyGuardrails",
    "NLExecutor",
]

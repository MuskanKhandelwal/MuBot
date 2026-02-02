# =============================================================================
# Agent Package
# =============================================================================
# The agent package contains the core intelligence of MuBot.
#
# Architecture Overview:
#   - Core: Main orchestrator that coordinates all components
#   - Reasoning: LLM interaction and decision-making logic
#   - Safety: Guardrails and ethical constraints
#
# The agent follows a structured workflow:
#   1. RECEIVE: User request comes in
#   2. RECALL: Load relevant memory and context
#   3. REASON: Plan approach and draft content
#   4. CHECK: Safety validation before any action
#   5. ACT: Execute approved actions
#   6. LEARN: Update memory with outcomes
# =============================================================================

from mubot.agent.core import JobSearchAgent
from mubot.agent.reasoning import ReasoningEngine
from mubot.agent.safety import SafetyGuardrails

__all__ = [
    "JobSearchAgent",
    "ReasoningEngine", 
    "SafetyGuardrails",
]

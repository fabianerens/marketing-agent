"""
YouTube Marketing Agent using Google ADK.

This agent orchestrates the complete analysis pipeline:
1. Channel resolution and data fetching
2. KPI calculation
3. Format mining and clustering
4. AI-powered recommendations
"""

from .agent import marketing_agent, root_runner, GEMINI_MODEL

__all__ = [
    "marketing_agent",
    "root_runner",
    "GEMINI_MODEL",
]

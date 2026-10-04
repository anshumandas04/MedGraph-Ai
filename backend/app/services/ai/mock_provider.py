"""Backward-compatible import; this now uses live document text, never canned text."""
from .local_provider import LocalRuleAIProvider


class MockAIProvider(LocalRuleAIProvider):
    """Deprecated alias for the local text-rule provider."""

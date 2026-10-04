"""Select an explicitly configured AI provider."""
from app.core.config import settings


def get_ai_provider():
    provider = settings.AI_PROVIDER.strip().lower()
    if provider in {"local", "rules", "mock"}:
        from .local_provider import LocalRuleAIProvider
        return LocalRuleAIProvider()
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("AI_PROVIDER=openai requires OPENAI_API_KEY. No document text was sent.")
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()
    raise ValueError(f"Unsupported AI_PROVIDER: {provider}")

"""Single source of truth for Google Gemini model selection.

Why this module exists
----------------------
`GEMINI_CHAT_MODEL` was read at five separate call sites with **four different**
hardcoded fallbacks:

    src/mcp_server/chat_interface.py:83   "gemini-3.6-flash"
    src/rag/rag_chain.py:93              "gemini-2.5-flash-lite"
    src/agents/summarizer.py:27          "gemini-1.5-flash"
    src/agents/agent.py:22               "gemini-1.5-flash"
    src/agents/multi_agent/agents.py:41  "gemini-3.1-flash-lite"

The root `.env` is gitignored (`.gitignore:4`), so a fresh clone has no `.env`
at all and every one of those fallbacks becomes the live value. The result was
a system that silently ran a different model in each phase.

Worse, `gemini-1.5-flash` **does not exist** on the Generative Language API --
verified against `models.list`, which returns 50 models for this key and no
`gemini-1.5-flash` among them. So on a fresh clone the Phase 3 ReAct agent and
its summarizer both requested a retired model and failed at call time.

`DEFAULT_CHAT_MODEL` is set to the value the shipped `.env` uses, because that
is the configuration the project has actually been exercised against.

Precedence, for both keys and models, keeps every alias that was already in
use so no existing deployment changes behaviour:
    GOOGLE_API_KEY      -> GEMINI_API_KEY
    GEMINI_CHAT_MODEL   -> GEMINI_MODEL   -> DEFAULT_CHAT_MODEL
"""

import os

# Verified present in models.list as of 2026-08-23.
DEFAULT_CHAT_MODEL = "gemini-3.1-flash-lite"
DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-2"

# Used only so that unit tests can construct a client without credentials.
# It is deliberately obvious: a real call with this value fails loudly rather
# than appearing to succeed.
TEST_PLACEHOLDER_KEY = "dummy_key_for_test"


def chat_model() -> str:
    """Resolve the chat/completion model name."""
    return (
        os.getenv("GEMINI_CHAT_MODEL")
        or os.getenv("GEMINI_MODEL")
        or DEFAULT_CHAT_MODEL
    )


def embedding_model() -> str:
    """Resolve the embedding model name."""
    return os.getenv("GEMINI_EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL


def api_key(allow_placeholder: bool = True) -> str:
    """Resolve the Google API key.

    `allow_placeholder=True` preserves the pre-existing behaviour of the agent
    and MCP modules, which construct their LLM client at import time and must
    not raise when no credential is configured (the test suites rely on this).
    Pass False where a missing credential should surface immediately.
    """
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if key:
        return key
    if allow_placeholder:
        return TEST_PLACEHOLDER_KEY
    raise RuntimeError(
        "No Google API key configured. Set GOOGLE_API_KEY (or GEMINI_API_KEY) "
        "in your .env -- see .env.example."
    )

import os
import sys
import pytest

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Set dummy Google API key for offline test predictability if not provided
if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = "dummy_test_api_key_for_phase4"

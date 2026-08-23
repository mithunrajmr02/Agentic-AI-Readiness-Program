import os

# Set dummy Google API key for offline test predictability if not provided
if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = "dummy_test_api_key_for_phase4"

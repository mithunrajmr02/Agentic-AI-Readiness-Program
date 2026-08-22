import sys
import src.agents.multi_agent.agents as _canonical

# Alias this module in sys.modules to canonical implementation
# This ensures unittest.mock.patch("multi_agent.agents._llm") or patch("multi_agent.agents.requests")
# patches the exact active module used by all agent nodes.
sys.modules[__name__] = _canonical

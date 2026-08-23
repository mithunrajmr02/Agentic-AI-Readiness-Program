"""The Phase 3 agent must be reachable from the application, not just from pytest.

Why this file exists
--------------------
For the whole history of this project the Phase 3 ReAct agent was fully implemented,
fully tested, and completely unreachable. `run_agent` had exactly two callers: its
own unit tests and a standalone CLI script. No screen a user could open ever invoked
it -- the Streamlit sidebar did not even list Phase 3 among the active phases.

Every Phase 3 unit test still passed the entire time. They assert that the tools
work and that the executor can be built; none of them asserts that anything in the
running application ever calls it. That is the gap this file closes.

`streamlit.testing.v1.AppTest` executes the real app script and surfaces whatever it
rendered, so these tests fail if the tab is deleted, if the agent stops being wired
to it, or if a tool is registered in the executor but never surfaces to the user.
"""

import os
import pytest

streamlit_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = streamlit_testing.AppTest

# The key lives in .env and is loaded by `load_dotenv()` inside the modules under
# test, not exported into the shell. Without this the skip below would fire on every
# run and these tests would never once execute -- a test that always skips protects
# nothing.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - python-dotenv is a hard dependency here
    pass

APP = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "src", "ui", "chat_streamlit", "app.py",
)

# Rendering the app constructs the Gemini clients for both the agent and the RAG
# chain. Without a key that is an environment limitation, not a defect, so skip
# rather than report a false failure.
requires_key = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="rendering the app builds the Gemini-backed agent and RAG chain; no GOOGLE_API_KEY set",
)


@pytest.fixture(scope="module")
def rendered_app():
    """Run the real Streamlit script once and share the result across these tests."""
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    return at


@requires_key
def test_the_app_renders_without_error(rendered_app):
    """A tab that raises on import is a tab nobody can use."""
    assert not rendered_app.exception, \
        f"app raised while rendering: {[str(e.value) for e in rendered_app.exception]}"
    assert not rendered_app.error, \
        f"app rendered an error box: {[str(e.value)[:300] for e in rendered_app.error]}"


@requires_key
def test_the_phase_3_agent_has_a_tab_in_the_running_app(rendered_app):
    """The check that would have caught the original disconnection."""
    labels = [str(getattr(t, "label", "")) for t in rendered_app.tabs]
    assert any("Phase 3" in label for label in labels), \
        f"no Phase 3 tab in the app; tabs are {labels}"


@requires_key
def test_the_sidebar_lists_phase_3_as_active(rendered_app):
    """The app previously advertised phases 2, 4 and 5 and silently omitted 3.

    Scoped to the sidebar deliberately. Asserting against every markdown block in
    the app would pass on the words "Phase 3" appearing in the tab's own greeting
    text, which is not what this test claims to check.
    """
    sidebar_text = " ".join(m.value for m in rendered_app.sidebar.markdown)
    assert "Phase 3" in sidebar_text, \
        f"sidebar does not list Phase 3 as active: {sidebar_text[:400]}"


@requires_key
def test_every_registered_tool_is_visible_to_the_user(rendered_app):
    """A tool the UI never names is a capability the user cannot know they have.

    This also pins tab and executor together: if a tool is added to
    `build_agent_executor` but the tab is left behind, this fails.
    """
    from src.agents.agent import build_agent_executor

    registered = {t.name for t in build_agent_executor().tools}
    body = " ".join(m.value for m in rendered_app.markdown)

    missing = sorted(name for name in registered if name not in body)
    assert not missing, f"registered but not shown in the UI: {missing}"


@requires_key
def test_typing_in_the_tab_actually_invokes_the_agent():
    """The tab must call the agent, not merely look like it does.

    This is the test the others could not replace. Every assertion above still
    passed when `run_agent(...)` in the tab body was swapped for the literal string
    "Not implemented." -- the tab rendered, the label was right, the tools were
    listed, and nothing reached the agent. A tab that displays a canned string is
    the "agent that is never invoked" defect wearing the UI of a working one.

    So this drives the real widget and asserts on the call itself: the user's text
    reaches `run_agent`, and `run_agent`'s return value reaches the transcript.
    """
    from unittest.mock import patch

    import src.agents.agent as agent_mod

    sentinel = "SENTINEL-AGENT-REPLY-9f3c"
    question = "What is the total value of our current inventory?"

    at = AppTest.from_file(APP, default_timeout=180)

    # The app does `from src.agents.agent import run_agent` at module scope, and
    # AppTest re-executes that script on every run, so patching the attribute on the
    # module before running is what the script will bind.
    with patch.object(agent_mod, "run_agent", return_value=sentinel) as mock_run:
        at.run()
        at.chat_input(key="p3_input_box").set_value(question).run()

    assert mock_run.called, "the Phase 3 tab never called run_agent"
    passed_query = mock_run.call_args.args[0]
    assert passed_query == question, \
        f"the tab sent {passed_query!r} to the agent instead of the user's question"

    # The executor is passed in rather than rebuilt per message.
    assert mock_run.call_args.args[1] is not None, \
        "the tab called run_agent without an executor, forcing a rebuild per message"

    rendered = " ".join(m.value for m in at.markdown)
    assert sentinel in rendered, "the agent's answer was never rendered to the user"


@requires_key
def test_an_agent_failure_is_rendered_as_a_failure_not_an_answer():
    """`run_agent` returns its errors as a string; they must not read as answers.

    Without this the tab would render a stack trace with `st.markdown` and append it
    to the transcript, where it becomes indistinguishable from something the agent
    concluded -- the same defect that was already fixed in the Phase 2 RAG tab.
    """
    from unittest.mock import patch

    import src.agents.agent as agent_mod
    from src.agents.agent import AGENT_ERROR_PREFIX

    failure = f"{AGENT_ERROR_PREFIX} ResourceExhausted: 429"

    at = AppTest.from_file(APP, default_timeout=180)
    with patch.object(agent_mod, "run_agent", return_value=failure):
        at.run()
        at.chat_input(key="p3_input_box").set_value("anything").run()

    error_text = " ".join(str(e.value) for e in at.error)
    assert failure in error_text, \
        "an agent failure was not rendered as an error box"
    assert failure not in " ".join(m.value for m in at.markdown), \
        "the failure was also rendered as normal markdown, which reads as an answer"

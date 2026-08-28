"""tests/autonomy -- WS-8's own tests (not graded; tests/phase5 is graded and
untouched). Proves the properties 14-PARALLEL-WORKSTREAMS.md §"WS-8" and
18-INTEGRATION-AND-TESTING.md §4.3 ask for: the 8-node topology, the
durable interrupt suspending and resuming (including across a real process
restart -- test_restart.py), and the executor re-checking preconditions
rather than trusting proposal-time state.
"""

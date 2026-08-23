"""Test-suite-wide path setup.

Every graded suite imports the application as `src.*`, which only resolves when
the repository root is on `sys.path`. Under `--import-mode=importlib` pytest adds
nothing to `sys.path` itself, and the four suites previously each carried their own
copy of this insert (plus inserts for the now-deleted `phaseN/` bridge packages).
One conftest at the tests root replaces all of them.
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

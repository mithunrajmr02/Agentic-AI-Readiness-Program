"""Steward foundations — the frozen shared contracts (WS-0).

Every downstream workstream imports from this package. The modules here are the
system's single sources of truth for:

* ``clock``  — the only source of "now" (real wall clock + simulation offset)
* ``vocab``  — the frozen status vocabularies and the analysis-status projection
* ``errors`` — the exception taxonomy every layer raises
* ``events`` — the synchronous in-process event bus
* ``ids``    — concurrency-safe sequential business identifiers

These contracts are published exactly as specified in
``docs/implementation/15-SHARED-CONTRACTS.md`` (frozen). Nothing here should grow
a feature that document does not mandate.
"""

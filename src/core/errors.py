"""The Steward exception taxonomy.

15-SHARED-CONTRACTS.md §2.6. Every layer raises these; the API error envelope
(§12.3) maps them to HTTP responses (§12.4): ``InsufficientData`` → 422 (never
500), ``PolicyDenied`` → 403, ``PreconditionFailed`` → 409, ``ExecutionFailed``
→ 5xx. Each subclass exposes a stable ``code`` so the envelope builder never has
to branch on the exception type by hand, plus the structured fields the envelope
requires (``needed``/``have`` for insufficient-data, ``citation`` for denials).
"""


class StewardError(Exception):
    """Base class for every domain error the system raises deliberately."""

    code = "steward_error"


class InsufficientData(StewardError):
    """Raised when the evidence is too thin to compute or act (§12.4 → 422).

    ``what`` is the thing that could not be produced, ``needed`` and ``have`` are
    the human-readable evidence gap surfaced verbatim in the 422 body.
    """

    code = "insufficient_data"

    def __init__(self, what: str, needed: str, have: str):
        self.what = what
        self.needed = needed
        self.have = have
        super().__init__(f"Insufficient data for {what}: needed {needed}, have {have}")


class PolicyDenied(StewardError):
    """Raised when an autonomy policy forbids an action (§12.4 → 403).

    ``citation`` is the verbatim manual sentence that grounds the denial, or
    ``None`` when the denial is structural (e.g. the kill switch) rather than a
    manual rule.
    """

    code = "policy_denied"

    def __init__(self, rule: str, citation: str | None):
        self.rule = rule
        self.citation = citation
        detail = f"Policy denied by rule '{rule}'"
        if citation:
            detail = f"{detail}: {citation}"
        super().__init__(detail)


class PreconditionFailed(StewardError):
    """Raised when the world is not in the state an action requires (§12.4 → 409)."""

    code = "precondition_failed"

    def __init__(self, precondition: str, detail: str):
        self.precondition = precondition
        self.detail = detail
        super().__init__(f"Precondition failed ({precondition}): {detail}")


class ExecutionFailed(StewardError):
    """Raised when a side-effecting action fails partway (e.g. supplier gateway)."""

    code = "execution_failed"

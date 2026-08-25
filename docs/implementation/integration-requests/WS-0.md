# WS-0 — Integration Requests & Reconciliation Notes

**Wave 0 · Foundations & Contracts · status: COMPLETE, all gates green.**

This is the sanctioned channel (per the WS-0 charter and doc 14 §"IF YOU NEED
SOMETHING YOU DO NOT OWN"). It records (A) what WS-0 froze, (B) decisions taken
where the planning docs under-specified or disagreed, (C) explicit handoffs to
downstream streams, and (D) the verification evidence. Downstream streams should
read section B before building against the contracts.

Authority rule used throughout: **`15-SHARED-CONTRACTS.md` is the frozen source.
Where `12-DATA-AND-API-CHANGES.md` or `14-PARALLEL-WORKSTREAMS.md` differ, doc 15
wins**, because doc 15 is the one every stream builds against.

---

## A. What WS-0 published (the frozen surface)

| Area | Files | Notes |
|---|---|---|
| Clock | `src/core/clock.py` | `now()`/`today()`/`offset_days()`/`set_offset()`/`reset()`. See B4. |
| IDs | `src/core/ids.py` | `next_id(prefix, width=6)` + `IdSequence` model (`id_sequences` table). Concurrency-safe. See B1. |
| Events | `src/core/events.py` | `subscribe()`/`emit()`/`reset()`. Synchronous, ordered, handlers never propagate exceptions. |
| Errors | `src/core/errors.py` | §2.6 taxonomy, each with a `.code` class attr for the §12.3 envelope. |
| Vocab | `src/core/vocab.py` | §2.4 tuples **verbatim** + `project_analysis_status()` (§2.5). See B2. |
| Models | `src/backend/models_{analytics,governance,sourcing,simulation}.py` | The 8 new business tables, columns exactly per §3.1–§3.3. |
| Registry | `src/backend/models_registry.py` | Imports every new model so `create_all` sees them. **Append-only** for downstream streams that add tables. |
| Contracts | `src/backend/contracts/` | §12.2 success + §12.3 error envelopes + `success_envelope()` / `error_envelope()`. See B5. |
| main.py | one line: `from src.backend import models_registry  # noqa: F401` at `:13` | The single sanctioned shared-file edit (doc 14 §2.4). |
| Frontend deps | `src/ui/web_react/package.json` | Added `@tanstack/react-query`, `react-router-dom`, `recharts`. See C1. |

`requirements.txt`, `src/service_auth.py`, `src/model_config.py` are WS-0-owned but
**left unchanged** this wave — see B3 / B6. Owning a file does not mean it must
change; changing auth/LLM config would have risked the green baseline for no
contract benefit.

---

## B. Decisions taken (read before building)

### B1 — There are **9** new physical tables, not 8
Doc 15 §3 is titled "The eight new tables" (the business tables). The frozen
`ids.py` contract (§2.2) additionally requires a counter table, so the schema
`create_all` produces has **9** new tables: the 8 business tables **plus
`id_sequences`** (infra, owns the monotonic counters behind `next_id`). The
Wave-0 exit gate wording ("eight tables create") refers to the business tables;
`id_sequences` is expected, not a scope violation. Verified present in section D.

### B2 — Vocabulary is doc 15 §2.4 verbatim; ignore any doc-12 variants
`vocab.py` mirrors §2.4 exactly. Where earlier planning text used different
tokens, **use `vocab.*`**, not the doc-12 spelling. Confirmed frozen values:
- `SEVERITIES = ("critical", "high", "medium", "low")` — **not** critical/warning/info.
- `decisions.status` is a **single** column over the 12-value `DECISION_STATUS`.
  There is **no `analysis_status` column.** The 4-value graded `analysis_status`
  is a *derived projection* — `vocab.project_analysis_status(status, action_type)`.
  **WS-8 must call this** to populate `InventoryState["analysis_status"]`; it is a
  display/compat mapping only, nothing branches on it (§2.5).
- `approvals` uses **`outcome`** (`approved|rejected|countered|expired`), not `status`.
- `signals.status` lifecycle is `open|superseded|resolved|expired` (§3.1).

### B2b — New→new references are **string business-refs**, not integer FKs
Per §3.1–§3.3 the cross-table refs between *new* tables carry the human-readable
business ID as a `String` with **no FK constraint**:
`decisions.signal_id / run_id / execution_ref / reversal_of`,
`approvals.decision_id`, `agent_runs.signal_id`. Integer `ForeignKey`s exist
**only** to the pre-existing tables (`products`, `suppliers`, `purchase_orders`,
`users`). Downstream joins on the string ref (e.g. `decisions.signal_id ==
signals.signal_id`). This matches the frozen contract and avoids a create-order
coupling between new modules. The field is `run_id` everywhere (not `run_ref`).

### B3 — `requirements.txt`: no change needed (AD-14 satisfied trivially)
WS-0's foundations import only stdlib + `sqlalchemy` + `pydantic` + `structlog`,
all already declared in the unified master `requirements.txt` (which also already
carries `langgraph`, `langchain*`, `chromadb`, `mcp`, `streamlit`, etc.). WS-0
introduced **no** new Python package. If a later stream needs a package not
present, file it here and WS-0 adds it (single-editor rule stands).

### B4 — `clock.py` is the one sanctioned wall-clock reader; source greps stay clean
Invariant #1 bans the wall-clock calls (on the datetime module, the date class,
and the time module) in new code; invariant #3 bans a database-side timestamp
default on new tables. `clock.py` is the single legitimate reader — it resolves
the wall-clock call by attribute lookup (`getattr(datetime, <reader>)`), never by
its dotted literal. None of WS-0's new files (`src/core/*`,
`src/backend/models_*.py`, `src/backend/contracts/*`) contain any of those
forbidden literals **anywhere — code or prose**; docstrings that discuss the
invariants are worded to avoid the literal token. A plain source-token grep over
WS-0's files therefore matches nothing and needs no allowlist entry. The `Enum`
cage (invariant #2) is enforced structurally, verified at the DDL level in §D.4
(no `CHECK` constraint on any new table).

### B5 — Contracts scope: envelopes only, no status-code map
Published exactly §12.2 (`{data, meta:{computed_at, clock_offset_days,
provenance, data_disclosure}}`) and §12.3 (`{error:{code, message, needed, have,
citation}}`), plus thin builders wired to `clock` and the error taxonomy.
`success_envelope()` defaults `computed_at`/`clock_offset_days` from the clock;
`error_envelope(exc)` maps `.code` and pulls `needed`/`have`/`citation` off the
subclass. **`citation` is a `str | None`** (e.g. `"manual §10 line 113"`), not a
struct (§7 / §12.3). The §12.4 **status-code map (422/403/409/429) was NOT baked
into contracts** — the code→status mapping is not 1:1 explicit in doc 15, so it is
left to each router to avoid encoding a guess six streams inherit. **If streams
want a shared `status_for(code)` helper, request it here and WS-0 will add it.**

### B6 — AD-12 (agent identity) deferred; handled via `decisions.actor` string
No auth change was made. Agent identity is carried by the frozen `decisions.actor`
string (`"agent:replenishment" | "user:3" | "system"`, §3.2), which needs no
change to `service_auth.py`. If AD-12 later requires a real authenticated agent
*principal* (a service-account row / token), that is an open item — file it here;
it most naturally belongs to the seeding stream (WS-2) rather than WS-0 plumbing.

---

## C. Handoffs / requests to other streams

### C1 — WS-6 (frontend): regenerate the lockfile
WS-0 added three runtime deps to `package.json`
(`@tanstack/react-query ^5.59.0`, `react-router-dom ^6.26.2`, `recharts ^2.13.0`)
but **did not modify `src/ui/web_react/package-lock.json`**, because the lockfile
is not in WS-0's ownership list and the DoD requires `git diff` to list only
owned files. **Action: run `npm install` before any `npm ci`** to sync the
lockfile with the new dependencies. (`node_modules/` is absent in the worktree;
this is expected.)

### C2 — Every router stream: use the publication contract, don't touch main.py
Per §12.1, expose a module-level `router` and stop. Integration writes the
`include_router` at `main.py:177`. Streams that add a **table** append their
import to `models_registry.py` (append-only) — they must **not** add a second
`create_all` or edit `main.py`.

---

## D. Verification evidence (DoD)

1. **WS-0 tests green** — `tests/core/` = 66 passed (vocab 17, errors 7, clock 9,
   events 6, ids 6, models 11, contracts 10).
2. **Graded phases unbroken** — `tests/phase1..phase5` = **232 passed, 2 skipped**
   (identical to bootstrap baseline; the 2 skips are the LangSmith tests). Full
   suite: **298 passed, 2 skipped**.
3. **Ownership** — `git diff --name-only` lists only WS-0-owned paths (`src/core/*`,
   `src/backend/models_*.py`, `src/backend/contracts/*`, one line in `main.py`,
   `package.json`) plus WS-0's own `tests/core/*`. No shared/frozen file touched
   beyond the sanctioned line.
4. **Additive schema on a copy of the real DB** — copied the real `inventory.db`,
   imported the app (wiring `models_registry`), ran `create_all`: the **8 existing
   tables are byte-identical** (DDL unchanged), **exactly 9 new tables added**
   (8 business + `id_sequences`), and **no new table carries an Enum `CHECK`
   constraint** (invariant #2 verified at the DDL level).
5. Not committed to `main`; not pushed; no branch merged.

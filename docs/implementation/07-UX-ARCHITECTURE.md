# 07 — UX Architecture

> **Status:** Proposal. Nothing here is approved.
> **Purpose:** Design the product experience from scratch where necessary, per the brief's instruction to treat the current UI as a POC. Covers the landing experience, navigation, dashboards, operational screens, agent interaction, approvals, exceptions, decision history, impact and executive views, how agent actions are communicated, and how the live demo flows through the UI.
> **Standard to meet, verbatim from the brief:** *"a modern, coherent product experience—not an obviously AI-generated collection of screens."*

---

## 1. The standard, stated as a testable rule

"Not obviously AI-generated" is a real constraint, and it is testable if you name the tells. These are the specific patterns that mark a screen as machine-produced, and each is banned by name.

| Tell | Why it reads as generated | The rule here |
|---|---|---|
| Four KPI cards in a row, identical, icon top-right | The layout was chosen before anyone asked which numbers matter | **Metrics earn their size.** No metric row without a hierarchy: one lead figure, supporting figures smaller |
| Purple/indigo gradient hero | The default palette of every template | One neutral base, one accent, three semantic states. Gradients only inside data visualisation |
| Emoji in headings | Filler where a real label was needed | No emoji in UI chrome. Icons are `lucide-react`, already a dependency |
| "Welcome back, Anita 👋" | A greeting where the work should be | The landing page opens on **what needs a human**, not on a salutation |
| Every panel a rounded card with a shadow | Uniform elevation destroys hierarchy | Two elevation levels only. Tables sit on the page surface, not in cards |
| Glassmorphism / blur | Decoration mistaken for design | None |
| Sidebar of eight equal items | No sense of which destinations matter | Navigation is **grouped by job**, with the primary destination visually dominant |
| Same font size everywhere | Nothing is important, so nothing reads | A four-step type scale, used strictly |
| Charts that show what the number already said | Volume standing in for insight | A chart must show a **shape over time** or a **comparison**. Otherwise it is a number |
| Placeholder "Analytics coming soon" | Scaffolding shipped as product | Nothing ships stubbed. A screen either works or is not in the nav |

**The positive version of the rule:** the screen should look like it was built by someone who has watched Anita work. Dense where she scans, spacious where she decides, and silent where there is nothing to say.

### 1.1 What the current UI actually is

Verified, not assumed:

- **1,136 lines** in a single `App.jsx`, 5 nav destinations, 5 modals, **zero** AI features.
- Navigation is `const [activeTab, setActiveTab] = useState('dashboard')` at `App.jsx:160`. **There is no router.** No URL changes, nothing is linkable, the back button does nothing.
- Dependencies are exactly four: `axios ^1.7.2`, `lucide-react ^0.395.0`, `react ^18.3.1`, `react-dom ^18.3.1`. **No charts library. No server-state library. No router.**
- The AI lives in a **separate Streamlit application** with no connection to any of it.

So this is not a re-skin. Routing, server state, and charts are being **introduced**, and the intelligence and the product are being merged into one application for the first time. WS-6 must be scoped accordingly.

### 1.2 What is kept

Rewriting 1,136 lines of working forms, modals, validation, and error handling would be vandalism. The existing CRUD is **decomposed into components and re-skinned**, not replaced (AD-10). The extraction is mechanical and is the single serialisation point in the UI workstream — see [16-DEPENDENCY-GRAPH.md](16-DEPENDENCY-GRAPH.md).

---

## 2. The organising idea

> **Steward is a control tower, not a dashboard.**

A dashboard answers *"how are things?"* A control tower answers *"what needs me, and what has already been handled?"* Every layout decision below follows from that one sentence.

Three consequences:

1. **Exceptions outrank totals.** The landing page leads with signals and approvals. Inventory totals are available, not featured.
2. **The agent's work is visible as work.** Not a chat log — a stream of decisions with authority paths and outcomes.
3. **Provenance is chrome, not a feature.** Every number carries how it was derived. This is the design expression of C2, and it is why "where did that come from?" never needs asking.

---

## 3. Information architecture

### 3.1 Navigation, grouped by job

Eight destinations is too many as a flat list. Grouped by the job they serve, it reads:

```
STEWARD                                      [mode: assisted ▾]  [◼ STOP]  AS

  OPERATE          ← the daily loop
    ▸ Control Tower          ⌘1     ← default landing
    ▸ Signals            3   ⌘2     ← badge = open, severity-coloured
    ▸ Approvals          1   ⌘3     ← badge = pending (manager only)

  MANAGE           ← the records
    ▸ Inventory              ⌘4
    ▸ Suppliers             ⌘5
    ▸ Receiving             ⌘6     ← staff-visible; narrow by design

  PROVE            ← the evidence
    ▸ Decisions             ⌘7
    ▸ Impact                ⌘8

  ─────────────────────────────────
    ▸ Agent Console  ↗              ← internal; visually de-emphasised
```

Decisions embedded in that structure:

- **Three groups, not eight items.** OPERATE / MANAGE / PROVE maps to the product's own pillars (SENSE / ACT / PROVE), so navigation teaches the model of the product.
- **Control Tower is the default route**, and the only destination with no badge — because it contains everything the badges point at.
- **Badges only where a count implies action.** Inventory has no badge; a product count is not a to-do.
- **Approvals is hidden for staff**, not disabled. RBAC shapes the navigation, so the nav is itself evidence that roles are enforced.
- **Autonomy mode is in the header**, permanently. The single most important piece of state in the product should never require navigation to find.
- **The kill switch is in the header**, on every screen, for every role. Reaching for it should never require thought.
- **Agent Console is last, marked external.** Streamlit is demoted to an internal inspection tool (AD-10) and the visual treatment says so.

### 3.2 URL scheme

Routing is being introduced, so the URL scheme is a design decision rather than an accident.

| Route | Screen | Notes |
|---|---|---|
| `/` | → `/tower` | |
| `/tower` | Control Tower | Default landing |
| `/signals` | Signals inbox | `?type=`, `?severity=`, `?status=` |
| `/signals/SIG-000045` | Signal detail | **Linkable.** Paste into chat and the recipient sees the same case |
| `/approvals` | Approval queue | Manager only |
| `/approvals/APR-000012` | Approval detail | |
| `/inventory` | Product list | |
| `/inventory/:sku` | Product detail | Velocity, ROP audit, movement history |
| `/suppliers` | Supplier list | |
| `/suppliers/:id` | Scorecard | Reliability, price history, open POs |
| `/receiving` | Receiving queue | |
| `/receiving/PO-2026-0042` | Receipt entry | Partial + backdate |
| `/decisions` | Decision timeline | Filterable |
| `/decisions/DEC-000123` | Decision detail | Full reasoning record |
| `/impact` | Impact view | |
| `/settings/autonomy` | Autonomy policies | Manager only |
| `/settings/scenarios` | Demo scenarios | Manager only |

**Every ID is addressable.** `SIG-000045`, `DEC-000123`, `APR-000012`, `PO-2026-0042` — the human-readable ID conventions exist so that a URL can be pasted into a message and mean something. In a governance product this is not a nicety: an audit conversation is conducted in references.

---

## 4. Design system

Small, opinionated, and enforced by CSS custom properties in one file — which is also what makes parallel UI work safe.

### 4.1 Colour

```
--surface-0    #FFFFFF   page
--surface-1    #F7F8FA   panels, table headers
--surface-2    #EDEFF3   hover, selected
--border       #DFE3E8
--ink-1        #14181F   primary text
--ink-2        #556070   secondary
--ink-3        #8792A2   tertiary, labels
--accent       #1A56DB   interactive, links, primary buttons
--critical     #C4262E   out-of-stock, overdue, failed
--warn         #B54708   threshold breach, pending, expiring
--good         #05603A   executed, on-time, sufficient
--agent        #5B21B6   agent-authored content ONLY
```

Two decisions worth defending:

**One accent, not a palette.** `--accent` is for interaction. Semantic colour is for state. When these blur, a user cannot tell "clickable" from "urgent" — the most expensive confusion in an operational tool.

**`--agent` is reserved.** A single hue, used nowhere except to mark content a language model produced. Not decoration — a **provenance channel**. See §7.

### 4.2 Type

Four steps. Anything else is a mistake.

```
--t-display   28/34  600   page titles, the one lead metric
--t-heading    18/26  600  section headings, card titles
--t-body       14/22  400  everything
--t-meta       12/18  500  labels, timestamps, provenance, badges
--t-mono       13/20  450  IDs, formulas, SKUs, quantities
```

Numerals are tabular everywhere (`font-variant-numeric: tabular-nums`). A column of quantities that does not align is a column nobody trusts.

### 4.3 Spacing and density

4px base. Two densities: **compact** for tables (32px rows), **comfortable** for decision surfaces (44px targets). Anita scans tables; the Store Manager reads decisions. Same product, different job, different density.

### 4.4 Elevation

Two levels. `--surface-1` panels with a 1px border, and one true shadow reserved for modals and the co-pilot drawer. No shadow on tables, rows, or metrics.

---

## 5. The screens

### 5.1 Control Tower — `/tower`

The landing experience. Answers the control-tower question in one screen, top to bottom, in priority order.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Control Tower                          Tue 25 Aug, 09:12 · tick 08:00 ✓  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  NEEDS YOU                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ ▲ APR-000012   PO-2026-0051 · ₹68,400 · Bluetooth Speaker          │  │
│  │   Above ₹50,000 — §10 requires Store Manager approval              │  │
│  │   waiting 2h 14m of 24h                          [ Review → ]      │  │
│  ├────────────────────────────────────────────────────────────────────┤  │
│  │ ▲ SIG-000047   config_drift · USB-C Cable                          │  │
│  │   Reorder point 20; measured demand implies 47                     │  │
│  │   detected 08:00                                 [ Review → ]      │  │
│  ├────────────────────────────────────────────────────────────────────┤  │
│  │ ● SIG-000046   po_overdue · PO-2026-0038 · 2 days late             │  │
│  │   Sharma Electronics · promised 23 Aug                             │  │
│  │   detected 08:00                                 [ Review → ]      │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  HANDLED WHILE YOU WERE AWAY                            last 24h         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ ✓ 08:00  DEC-000123  Ordered 120 × Wireless Mouse from Kumar       │  │
│  │          Trading · ₹14,400 · within authority                      │  │
│  │          projected_breach — 8 days cover, 11-day lead     [ ↗ ]    │  │
│  │ ✓ 08:00  DEC-000124  Declined to order Laptop Stand                │  │
│  │          insufficient history — 2 sale events in 90 days  [ ↗ ]    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  POSITION                                                                │
│   3 signals open   ·   1 pending approval   ·   4 POs in transit         │
│   1 overdue   ·   ₹1.24L inventory value   ·   18 days cover (median)    │
│                                                                          │
│  ┌─ 90-day signal volume by type ───────────────────────────────────┐    │
│  │  ▁▂▁▃▂▄▃▂▅▃▂▁▂▃▄▃▂▁▃▂                                            │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ⓘ Demonstration data — 90-day history is simulated. Mechanism is real.  │
└──────────────────────────────────────────────────────────────────────────┘
```

Every choice here is deliberate:

- **"NEEDS YOU" is first and cannot be scrolled past.** The zone is empty when nothing needs a human — and an empty state that says *"Nothing needs you. 4 decisions handled since 08:00."* is the most valuable screen in the product.
- **"HANDLED WHILE YOU WERE AWAY" is the differentiating zone.** No baseline POC has anything to put in it, because no baseline POC does anything unprompted. It is the visual proof that the system initiates.
- **A refusal is displayed with equal weight to an action.** `DEC-000124` — *declined, insufficient history* — sits beside the order it did place. A system that only shows its successes is advertising; showing the decline is what makes the rest believable.
- **"POSITION" is a single line of text, not four cards.** These numbers are context, not tasks. Giving them card-sized real estate is exactly the generated-dashboard tell from §1.
- **One chart, and it shows a shape over time.** Signal volume across 90 days is genuinely a shape. Inventory value is a number and stays a number.
- **The synthetic-data disclosure is on the landing page**, not buried. Per C8 §7 this is mandatory — and volunteering it is stronger than being caught by it.
- **Tick status in the header** (`tick 08:00 ✓`) is how the system proves it is running when nobody is watching.

### 5.2 Signals — `/signals`

Triage. Dense, keyboard-driven, one row per signal.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Signals            [ open ▾ ] [ all types ▾ ] [ all severity ▾ ]    3    │
├──────────────────────────────────────────────────────────────────────────┤
│  SEV  ID          TYPE              SUBJECT           DETECTED   STATUS  │
│  ▲    SIG-000047  config_drift      USB-C Cable       08:00      open    │
│  ●    SIG-000046  po_overdue        PO-2026-0038      08:00      open    │
│  ○    SIG-000045  projected_breach  Wireless Mouse    08:00      resolved│
│                                                       └ DEC-000123 ↗     │
└──────────────────────────────────────────────────────────────────────────┘
```

A resolved signal **links to the decision that resolved it**. This is the structural fix for W6 — today `check_stock_alerts` resolves and reinserts on every call, so `is_resolved` means "superseded" and no endpoint reads the table at all. Here, resolution means *a decision closed it*, and the decision is one click away.

Signal detail leads with **evidence**, because a signal a user cannot verify is a signal they will learn to ignore:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Signals                                                    SIG-000045  │
│                                                                          │
│  projected_breach · Wireless Mouse (SKU-1001)               ○ resolved   │
│  Detected 25 Aug 08:00:04 · 0.4s after the movement that caused it       │
│                                                                          │
│  WHY THIS FIRED                                                          │
│    on hand                          64 units                             │
│    average daily demand            5.8 units/day   ← 90d, 47 sale events │
│    supplier lead time                11 days       ← Kumar Trading       │
│    safety stock                    11.6 units      ← 2 days × 5.8        │
│    ─────────────────────────────────────────────────                     │
│    projected at lead time          0.2 units       64 − (5.8 × 11)       │
│    ≤ safety stock (11.6)           TRUE            → breach projected    │
│                                                                          │
│    ⓘ reorder_point = (average daily demand × lead time) + safety stock   │
│      Inventory Manual §3 "Reorder Point Calculation"              [ ↗ ]  │
│                                                                          │
│  ◈ WHAT'S HAPPENING                                          agent       │
│    Demand is steady, not spiking — 5.8/day against a 90-day mean of      │
│    5.6. The constraint is the 11-day lead time, which is longer than     │
│    the 8 days of cover on hand. No open PO covers this SKU.              │
│                                                                          │
│  RESOLVED BY                                                             │
│    DEC-000123 · ordered 120 units from Kumar Trading · ₹14,400     [ ↗ ] │
└──────────────────────────────────────────────────────────────────────────┘
```

Two things to notice. **The arithmetic is shown, not summarised** — `64 − (5.8 × 11) = 0.2`, with the manual section that supplies the formula and a link into the corpus. And **the agent's contribution is bounded and marked**: the `◈`-marked block interprets, it produces no numbers. That separation is C2 and C9's boundary rendered as layout.

### 5.3 Approval detail — `/approvals/:id`

The most important screen in the product. The Store Manager makes a real decision here, and the ordering of the page is the design argument.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Approvals                                    APR-000012 · waiting 2h14m│
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  THE AGENT WANTS TO                                                │  │
│  │  Order 240 × Bluetooth Speaker from Sharma Electronics             │  │
│  │  ₹68,400  ·  240 × ₹285  ·  expected 5 Sep (11-day lead)           │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  IT STOPPED BECAUSE                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ "Purchase Orders with a total value above ₹50,000 require formal   │  │
│  │  Store Manager approval prior to supplier submission."             │  │
│  │                        — Inventory Manual §10, PO Approval Threshold│  │
│  │                                                                    │  │
│  │  ₹68,400 > ₹50,000  →  requires_approval                           │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  HOW IT GOT HERE                                                         │
│    SIG-000048 threshold_breach · 22 on hand ≤ 40 reorder point     [↗]   │
│    quantity  240 = 12.0/day × (11 lead + 9 safety)         §9      [↗]   │
│    supplier  Sharma ₹285/11d  ·  alt: Kumar ₹302/7d               [↗]   │
│    data      sufficient — 90 days, 108 sale events                       │
│                                                                          │
│  ◈ THE SITUATION                                             agent       │
│    Demand has run 12.0/day for three weeks against a 90-day mean of      │
│    9.4 — a genuine step up, not noise. Sharma is the cheaper option      │
│    and has delivered 9 of 10 orders on time. Kumar is 6% dearer but      │
│    4 days faster, which would matter if this were urgent. It is not      │
│    yet: 22 units is ~2 days, but no stockout has occurred.               │
│                                                                          │
│  IF YOU DO NOTHING                                                       │
│    Stock reaches zero in ~2 days. The earliest possible delivery is      │
│    11 days out. Roughly 9 days of unmet demand at 12.0/day.              │
│    ⓘ Units, not rupees. Revenue impact needs per-SKU margin —           │
│      see Impact › what we cannot measure yet.                     [↗]   │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────────┐  │
│  │  Approve     │  │  Reject…     │  │  Change quantity or supplier… │  │
│  └──────────────┘  └──────────────┘  └───────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

The ordering is the whole design:

1. **What** — one sentence, largest type. A manager approving twenty of these needs the ask instantly.
2. **Why it stopped** — the quoted policy, styled as a quotation with its section. Not "exceeds threshold." The **sentence**, from their manual.
3. **How it got here** — the audit trail, compact, every element linkable.
4. **The situation** — agent-authored, marked, no new numbers.
5. **If you do nothing** — the counterfactual. This is what turns an approval from a chore into a judgment, and it is the field most approval UIs omit.
6. **Three doors**, equal weight. Approve is not a big green primary button — a UI that visually pushes toward approval is manufacturing consent, which in a governance product is a defect.

And the honesty detail in "IF YOU DO NOTHING": **units, not rupees**, with a link to the metric that would need client data. The temptation is to write "₹2.5L revenue at risk." It would be invented, and any buyer who has built a business case will know it.

Counter-proposal recomputes rather than accepts:

```
│  Change quantity                                                         │
│    240 → [ 120 ]                                                         │
│                                                                          │
│    ⟳ Recomputed                                                          │
│      value        ₹34,200  →  below ₹50,000, within agent authority      │
│      cover        10 days at 12.0/day, against an 11-day lead time       │
│      ▲ 120 units does not bridge the lead time. Expect a second          │
│        breach in ~10 days.                                               │
│                                                                          │
│    [ Approve 120 anyway ]   [ Keep 240 ]                                 │
```

The manager may still choose 120 — that is their authority. But the system states the consequence, and **records that it did**. "Approve anyway" over a stated objection is a materially different ledger entry from a plain approval, and C6 stores it as one.

### 5.4 Decisions — `/decisions`

The audit surface the manual asks for by name at §4 line 47 (*"Resolved alerts remain stored in the audit log for historical reporting"*).

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Decisions          [ all ▾ ] [ all outcomes ▾ ] [ 7 days ▾ ]             │
├──────────────────────────────────────────────────────────────────────────┤
│  25 Aug                                                                  │
│   09:14  DEC-000125  approved    Ordered 240 × Speaker      ₹68,400      │
│          Sharma · SIG-000048 · APR-000012 · approved by S. Iyer          │
│   08:00  DEC-000124  declined    No order — Laptop Stand         —       │
│          insufficient history: 2 sale events in 90 days                  │
│   08:00  DEC-000123  autonomous  Ordered 120 × Mouse        ₹14,400      │
│          Kumar · SIG-000045 · within authority (≤ ₹50,000)               │
│  24 Aug                                                                  │
│   14:22  DEC-000122  rejected    No order — Keyboard             —       │
│          rejected by S. Iyer: "existing stock in back room"              │
└──────────────────────────────────────────────────────────────────────────┘
```

Four outcome types shown with equal prominence: **autonomous / approved / rejected / declined**. Most agent products show only what the agent did. Showing what it was refused and what it refused itself is the difference between a log and an accountability record — and the `declined` rows are the ones that make the `autonomous` rows credible.

Decision detail is the immutable record: triggering signal, the exact computed inputs, the policy citation **as it read at decision time**, the agent's reasoning verbatim, the authority path, the human, the idempotency key, and the monitored outcome. A later edit to the manual cannot retroactively rewrite what governed a past decision — the citation is snapshotted, not resolved on read.

### 5.5 Impact — `/impact`

The executive view, and the screen where the package's honesty policy becomes visible design.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Impact                                                    [ 30 days ▾ ]  │
│                                                                          │
│  DETECTION                                                               │
│    Signals raised            47      threshold 18 · projected 12         │
│                                      overdue 6 · drift 8 · other 3       │
│    ▸ 14 of 47 are classes the previous system could not detect at all    │
│      (po_overdue, config_drift)                                          │
│    Median detection latency  0.6s    from the movement that caused it    │
│                                                                          │
│  DECISION                                                                │
│    Median decide-to-act      4m 12s                                      │
│    ┌────────────────────────────────────────────────────────────────┐    │
│    │  Manual expectation, Inventory Manual §10: within 24 hours     │    │
│    │  Observed: 4m 12s median (autonomous), 2h 41m (with approval)  │    │
│    │  ⓘ A documented baseline from your own manual — not an          │    │
│    │    industry estimate.                                          │    │
│    └────────────────────────────────────────────────────────────────┘    │
│    Autonomy rate             68%     32 of 47 resolved without a human   │
│    Approvals                 15      11 approved · 3 modified · 1 reject │
│    ▸ 20% modified — the agent's proposals are edited 1 in 5 times        │
│    Refusals                   6      4 insufficient data · 2 duplicate   │
│                                                                          │
│  METHOD                                                                  │
│    Fabricated numeric fields    5 → 0                                    │
│    ▸ forecast_units, confidence, recommended_qty, unit_price,            │
│      estimated_lead_time_days — all previously LLM-generated,            │
│      all now computed from the ledger with a cited formula.              │
│    Decisions with a policy citation      47 of 47   (100%)               │
│    Decisions with a full ledger record    47 of 47   (100%)              │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────────   │
│  WHAT WE CANNOT MEASURE YET                                              │
│                                                                          │
│    ₹ revenue protected                                                   │
│      formula   Σ (unmet units × unit margin) over avoided stockouts      │
│      needs     per-SKU margin · observed lost-sale rate                  │
│                                                                          │
│    Hours returned to the team                                            │
│      formula   (baseline minutes per cycle − observed) × cycles          │
│      needs     time-and-motion baseline for the current process          │
│                                                                          │
│    Stockout reduction                                                    │
│      formula   stockout-days, seeded behaviour vs agent behaviour         │
│      needs     real movement history · a holdout period                  │
│      status    available as a labelled simulation      [ Backtest → ]    │
│                                                                          │
│    ⓘ These are not estimates withheld. They are not computable from      │
│      the data available. Point Steward at real history and each one       │
│      becomes a number.                                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

**"WHAT WE CANNOT MEASURE YET" is the most persuasive block on the screen**, and it is counter-intuitive enough to state the reasoning. Every associate presenting an inventory POC will show a rupee figure. None of them will have per-SKU margin data, so every one of those figures is fabricated — and the people in the room who build business cases for a living will know it within seconds. Naming the formula, naming the missing input, and declining to guess is the only version of this screen that survives an informed question. It also converts a gap into a proposal: *point us at your history and we compute it.*

The `METHOD` block is unusual on an executive screen and belongs there. **5 → 0 fabricated fields** is verifiable by inspection, needs no client data, and is a claim about rigour rather than outcome — which makes it the most defensible number in the entire package.

### 5.6 Product detail — `/inventory/:sku`

Where C2 becomes concrete for a single SKU: the movement ledger as a chart, measured velocity with its window and sale count, configured versus computed reorder point side by side with the divergence named, days of cover, open POs, and the signal history for this product. If a `config_drift` signal is open, the proposed correction and its approval state appear inline.

The existing product CRUD is preserved here — decomposed out of `App.jsx`, re-skinned, with `PATCH /products/{id}` added for `reorder_point` and `safety_stock_days` (manager-gated, always via an approved C10 proposal).

### 5.7 Supplier scorecard — `/suppliers/:id`

Reliability from real delivery history — on-time rate, mean lateness, variance — using the criteria §6 line 74 names (*"price competitiveness, lead time reliability, quality compliance, and payment terms"*). Price and lead time per product from `supplier_products`, the table whose absence made `supplier_coordinator` structurally incapable of its own job. Open POs with overdue flagged.

The `active` flag is displayed prominently because §6 line 74 makes it an execution precondition: *"Procurement staff must verify a supplier is active before raising a PO."*

### 5.8 Receiving — `/receiving`

Dev Kumar's screen. Narrow on purpose — three fields, no dashboard.

```
│  PO-2026-0038 · Sharma Electronics · promised 23 Aug · ▲ 2 days late     │
│                                                                          │
│    Bluetooth Speaker      ordered 240      received [ 200 ]              │
│    Received on            [ 23 Aug 2026 ]  ← the day it actually arrived │
│                                                                          │
│    ⓘ 200 of 240 — the PO stays open for 40 units, and the shortfall      │
│      is recorded against Sharma's reliability.                           │
│                                                                          │
│    [ Record receipt ]                                                    │
```

Both fields are fixes to hard-coded behaviour: `received_date = date.today()` at `inventory_service.py:137` makes backdating impossible, and `qty = item.quantity_received or item.quantity_ordered` at `:140` makes partial receipt impossible. Without both, supplier reliability scoring is built on fiction — a Friday delivery keyed on Monday reads as three days late.

### 5.9 Autonomy settings — `/settings/autonomy`

Manager only. The mode dial per category with each mode's meaning stated in words rather than assumed; blast-radius caps with current headroom drawn as a bar; the retrieved policy threshold displayed **read-only with its citation** and a note that it lives in the manual; and a log of every mode change with who, when, and why.

The read-only threshold is a deliberate provocation. A manager may ask why they cannot edit it. The answer is the product's thesis: *because it is your operating manual's rule, not our setting. Change §10 and Steward follows.*

---

## 6. The co-pilot drawer

Not a tab. A drawer, `⌘K`, context-scoped to wherever it is opened.

```
┌───────────────────────────────────┐
│ Co-pilot          SIG-000045   ✕ │
├───────────────────────────────────┤
│ ◈ I have this signal, its evidence│
│   and the decision that resolved  │
│   it.                             │
│                                   │
│ ▸ why 120 and not 240?            │
│                                   │
│ ◈ 120 = 5.8/day × (11 lead + 9    │
│   safety) rounded to the pack of  │
│   10. 240 would be ~41 days of    │
│   cover against 18 days median    │
│   across the catalogue.           │
│   ⓘ §9 Reorder Quantity      [↗] │
│                                   │
│ ▸ order 300 more                  │
│                                   │
│ ◈ I can prepare it, but I cannot  │
│   place it. 300 × ₹120 = ₹36,000  │
│   is within the ₹50,000 limit,    │
│   but you are signed in as        │
│   warehouse staff and §10 assigns │
│   PO raising to the Procurement   │
│   Officer.                        │
│   [ Send to Anita for review ]    │
└───────────────────────------──────┘
```

Three properties that make this more than a chatbot:

- **It knows where it was opened.** On a signal it has the signal; on an approval it has the decision, the citation, and the computed inputs. Context injection is deterministic code, not a prompt asking the model to guess.
- **It has memory.** Currently `get_history_for_llm()` is defined and **never called**, so the existing chat cannot reason across two turns of the same conversation. Here it is called.
- **It cannot act outside policy.** A write request becomes a *proposal* entering the same governed pipeline as everything else. There is no privileged path — and the refusal above, which cites the role assignment rather than saying "permission denied," is the feature.

Built on the **MCP toolset**, not the Phase 3 executor, which is frozen at exactly 7 tools by `assert len(agent.tools) == 7` (`tests/phase3/test_phase3.py:15`). AD-11.

---

## 7. How agent actions are communicated

This is the genuinely novel design problem in the product, and it deserves its own rules. A user must be able to tell, at a glance and without reading carefully, **what a machine computed, what a language model said, and what a human decided.**

### 7.1 The three provenance marks

| Mark | Meaning | Treatment |
|---|---|---|
| *(none)* | Computed by deterministic code from the ledger | Normal ink. Hover reveals the formula and manual citation |
| **◈** | Authored by the language model | `--agent` left rule, `--agent` label, agent-tinted heading |
| **@** | A human decided this | Name, timestamp, and role shown inline |

Applied without exception. The consequence: a user can scan a decision and see instantly that the *numbers* are unmarked and the *narrative* is marked. Which is the truth — and it is AD-2 made visible.

This is also the direct antidote to the failure already recorded in the codebase. At `agents.py:389-406` the LLM invented `supplier_id: 101` and a price of ₹580.0 against a real ₹600.0. Under this scheme a price could never appear inside a `◈` block, because prices come from `supplier_products`. **The visual language enforces the architectural boundary.**

### 7.2 Announcing an action

Four states, four treatments:

| State | Language | Visual |
|---|---|---|
| Detected | *"Stock will cross the reorder point before a replacement can arrive."* | Severity dot, no action styling |
| Deciding | *"Computing quantity and comparing suppliers…"* | Inline progress, node-level |
| **Waiting on a human** | *"Prepared, not sent. ₹68,400 needs Store Manager approval — §10."* | `--warn` rule, SLA clock running |
| Acted | *"Ordered 120 × Wireless Mouse from Kumar Trading. PO-2026-0052 submitted."* | `--good` check, links to PO and decision |

**Past tense, specific object, named counterparty, resulting record.** Never *"action completed successfully"* — an operational user needs to know *what* happened, and the ID that proves it.

### 7.3 The three sentences that carry the product

Worth writing down as copy, because these are the moments a reviewer remembers:

> **Refusal on authority** — *"I prepared this order for ₹68,400 and stopped. §10 of your operations manual requires Store Manager approval above ₹50,000."*

> **Refusal on evidence** — *"I will not order this. 2 sale events in 90 days is not enough history to compute a defensible quantity. Here is what I would need."*

> **Action taken** — *"Wireless Mouse would have run out 3 days before the replacement arrived. I ordered 120 from Kumar Trading at 08:00. ₹14,400, within my authority. The reasoning is in DEC-000123."*

The first two are the product. Any competent POC can produce the third.

---

## 8. Empty, loading, error, and refusal states

Most POCs ship the happy path. These states are where an operational tool is judged.

| State | Design | Why |
|---|---|---|
| Nothing needs you | *"Nothing needs you. 4 decisions handled since 08:00."* + link to Decisions | The **best** state, and it should feel like an achievement, not a void |
| No signals ever | *"No signals yet. The next scheduled tick is 08:00 tomorrow."* | Explains *why* it is empty and when that changes |
| Insufficient data | Named as a first-class state with the failing condition and what is needed | This is C2's honesty made visible; hiding it would undo the point |
| Loading | Skeletons matching final layout; no spinners on tables | Layout shift on a table you are scanning is worse than a slower load |
| Agent thinking | Node-level progress: *"investigating → computing → checking policy"* | Shows the deterministic pipeline, which is reassuring rather than opaque |
| LLM unavailable | *"Narrative unavailable — the decision and its numbers are unaffected."* | **Critical.** Gemini's free tier is 15 RPM / 1,500 RPD. Degradation must be graceful and must make clear the *numbers* do not depend on the model |
| Kill switch engaged | Persistent header banner, all autonomy controls disabled, who and when | An unmissable global state |
| 403 | *"Warehouse staff cannot raise purchase orders. §10 assigns this to the Procurement Officer."* + escalate | An error that teaches the policy rather than just blocking |

The LLM-unavailable state deserves emphasis: it is the rate limit turned into a feature. When the narrative is missing but the decision, the numbers, and the policy check are all intact, the architecture has demonstrated its own claim — **the LLM is the explanation layer, not the decision layer.**

---

## 9. Frontend architecture

Designed for parallel development, since multiple Claude Code instances will build this.

```
src/ui/web_react/src/
  main.jsx                    router mount
  App.jsx                     shell only — nav, header, outlet
  design/
    tokens.css                ← WS-6 ONLY. Single source of truth
    primitives/               Button, Badge, Table, Panel, Metric, Modal,
                              Drawer, EmptyState, Skeleton, ProvenanceMark
  lib/
    api.js                    axios instance, auth, error normalisation
    queries/                  one file per domain — no cross-imports
    format.js                 currency, dates, quantities
  features/
    tower/          ← WS-11
    signals/        ← WS-12
    approvals/      ← WS-13
    decisions/      ← WS-13
    impact/         ← WS-14
    inventory/      ← WS-15  (decomposed from App.jsx)
    suppliers/      ← WS-15
    receiving/      ← WS-15
    copilot/        ← WS-16
```

The rules that make this safe in parallel:

1. **One owner per `features/` directory.** No instance edits another's feature folder.
2. **`design/` is WS-6's exclusively**, and it lands in Wave 1 before any feature work starts. Everyone consumes tokens and primitives; nobody adds to them.
3. **`App.jsx` becomes a shell.** Route registration is one line per feature, appended — an append-only file is the cheapest merge conflict to resolve.
4. **`lib/queries/` is one file per domain**, no cross-imports, so two instances never touch the same query file.
5. **The `App.jsx` decomposition is a Wave 1 serialisation point.** Extracting 1,136 lines is one instance's job and must complete before WS-15 starts. This is the genuine bottleneck in the UI plan and is acknowledged rather than wished away (see C7's partial feasibility mark in [04-OPPORTUNITY-SPACE.md](04-OPPORTUNITY-SPACE.md) §9.1).

### 9.1 The three new dependencies

| Package | Why | Alternative rejected |
|---|---|---|
| `react-router-dom` | There is **no router today** — `useState('dashboard')` at `App.jsx:160`. Addressable IDs are a governance requirement, not a convenience | Hand-rolled hash routing: no nested routes, no params, no history |
| `@tanstack/react-query` | Server state across ~20 endpoints with polling for signals and approvals. Hand-rolled `useEffect` fetching at this scale is where the bugs live | Manual state: cache invalidation after an approval touches four screens |
| `recharts` | Signal volume over 90 days, velocity trend, reliability history. Composable with React and small enough to justify | Chart.js: imperative, canvas, awkward inside React; D3: far too much for four charts |

Three additions. `axios` and `lucide-react` are **already present** and need nothing.

---

## 10. How the demo flows through the UI

The click path, with what is said and what the screen proves. Detail in [13-DEMO-SCENARIOS.md](13-DEMO-SCENARIOS.md).

| # | Screen | Action | The claim it proves |
|---|---|---|---|
| 1 | `/tower` | Land. Point at **HANDLED WHILE YOU WERE AWAY**. | It ran at 08:00 without being asked. **Autonomy.** |
| 2 | `/decisions/DEC-000124` | Open the **declined** row. | It refused on thin evidence. **Judgment, not compliance.** |
| 3 | `/signals/SIG-000045` | The **rice** signal — a different case. Evidence block: stored ROP 15 vs derived 44, measured lead time 9 vs contract 5, §3 citation. Two decisions from one signal: one executed, one pending. | Numbers are computed, not generated, and authority splits by the *kind* of change. **Grounding + insight.** |
| 4 | `/approvals/APR-000012` | Read the quoted §10 sentence aloud. | It reads the customer's manual. **Governance.** |
| 5 | *same* | Counter-propose 12 → 6. Show the recompute and the objection. | The human is in command; the system still advises. **Partnership.** |
| 6 | *same* | Approve. Watch the suspended graph resume and the PO reach `submitted`. | Durable interrupt, real state transition. **It closes the loop.** |
| 7 | Log in as staff → `/inventory` | Attempt a PO. Take the 403. | RBAC is enforced. **The 15-second test, volunteered.** |
| 8 | `/impact` | Scroll to **WHAT WE CANNOT MEASURE YET**. | We will not invent a rupee figure. **Credibility.** |

Eight steps, one browser tab, one application. Today this demo requires two applications and an explanation that they are the same product.

**The two steps most POCs will not have:** step 2 (a recorded refusal) and step 8 (a named, unfilled metric). Both are the product declining to overclaim, and both are more memorable than anything it does successfully.

---

## 11. Accessibility and craft

Not decoration — the difference between a product and a demo, and cheap if done from the start rather than retrofitted.

- Keyboard-complete. `⌘1`–`⌘8` for destinations, `⌘K` for the co-pilot, `j`/`k` and `Enter` in tables, `Esc` closes overlays. Anita is a keyboard user with a queue.
- Severity is never colour alone — dot **shape** (▲ critical, ● warning, ○ info) plus a text label. A red dot is invisible to ~8% of men.
- Contrast: 4.5:1 body, 3:1 large. `--ink-3 #8792A2` on `--surface-0` is the floor and is checked, not assumed.
- Focus is always visible. A 2px `--accent` ring, never `outline: none`.
- Tabular numerals in every numeric column.
- Live regions announce agent state changes so a screen-reader user is not surprised by a row appearing.
- Reduced-motion respected; transitions ≤150ms and never on data.

---

## 12. What is deliberately *not* built

| Not building | Why |
|---|---|
| A landing/marketing page | The product is the landing page. A hero section on an internal tool is theatre |
| Dark mode | Doubles token surface and visual QA for zero demo value. Tokens are structured so it is a later addition, not a rewrite |
| Mobile layouts | A second frontend while the first is being rebuilt. Responsive down to tablet; no phone-specific work |
| A chart on every screen | A chart must show a shape or a comparison. Four charts total, each earning its place |
| Notification toasts for agent actions | The Control Tower's HANDLED zone is the notification. Toasts vanish; a governance product needs a record |
| An onboarding tour | If the Control Tower needs explaining, the Control Tower is wrong |
| Customisable dashboards | Configurability is what you build when you do not know what matters. We do |
| Streamlit parity | Streamlit is demoted to internal inspection (AD-10). Rebuilding its tabs in React would be rebuilding the wrong product |

---

**Next:** [08-AGENTIC-WORKFLOWS.md](08-AGENTIC-WORKFLOWS.md) specifies the graph topology, node contracts, and the durable interrupt that makes the approval flow above technically real.

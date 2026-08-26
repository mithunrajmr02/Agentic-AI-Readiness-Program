# WS-6 — Integration Requests & Published Contracts

**Wave 1 · UI Foundation · status: COMPLETE, all tests green.**

## 1. What WS-6 Published

WS-6 owns the UI Foundation, design system tokens, client-side routing, shared primitives, layout shell, and `App.jsx` decomposition.

### 1.1 Design Tokens & Styles (`src/ui/web_react/src/styles/`)
- `src/ui/web_react/src/styles/tokens.css`:
  - **Surfaces**: `--surface-0` (`#FFFFFF`), `--surface-1` (`#F7F8FA`), `--surface-2` (`#EDEFF3`), `--border` (`#DFE3E8`).
  - **Inks**: `--ink-1` (`#14181F`), `--ink-2` (`#556070`), `--ink-3` (`#8792A2`).
  - **Semantics**: `--accent` (`#1A56DB`), `--critical` (`#C4262E`), `--warn` (`#B54708`), `--good` (`#05603A`).
  - **Agent Reserved Color**: `--agent` (`#5B21B6`) — reserved exclusively for LLM-authored content / provenance markers.
  - **Typography Hierarchy**: `--t-display` (28px/34px 600), `--t-heading` (18px/26px 600), `--t-body` (14px/22px 400), `--t-meta` (12px/18px 500), `--t-mono` (13px/20px 450).
  - **Tabular Numerals**: `font-variant-numeric: tabular-nums` globally enforced for numeric columns.
- `src/ui/web_react/src/index.css`: Imports `tokens.css` and sets standardized typography, tables, badges, form controls, and modal styles.

### 1.2 Core Libraries (`src/ui/web_react/src/lib/`)
- `src/ui/web_react/src/lib/api.js`:
  - Configured Axios instance with `API_BASE = 'http://localhost:8010/api/v1'` (conforming to Hard Rule: port 8010).
  - JWT Bearer token management (`TOKEN_STORAGE_KEY`, `applyToken`, `identityFromToken`).
  - Request interceptor attaching `Authorization: Bearer <token>`.
  - Error normalization helper: `describeApiError(err)`.
- `src/ui/web_react/src/lib/query.js`:
  - TanStack `QueryClient` configured with `refetchOnWindowFocus: false` and `staleTime: 10_000`.
  - **Frozen query key factories** (`QUERY_KEYS`) per `15-SHARED-CONTRACTS.md §13.2`:
    - `signals(filters)`: `['signals', filters]`
    - `signal(signalId)`: `['signal', signalId]`
    - `decisions(filters)`: `['decisions', filters]`
    - `decision(decisionId)`: `['decision', decisionId]`
    - `approvalsPending()`: `['approvals', 'pending']`
    - `approval(approvalId)`: `['approval', approvalId]`
    - `policies()`: `['policies']`
    - `impact()`: `['impact']`
    - `impactGaps()`: `['impact', 'gaps']`
    - `supplierScorecard(supplierId)`: `['supplier', supplierId, 'scorecard']`
    - `tower()`: `['tower']`
  - Cache invalidation helper: `invalidateAfterApproval(queryClient)`.
- `src/ui/web_react/src/lib/provenance.jsx`:
  - `formatINR(val)`: Formats numeric rupee values with `₹` and Indian number numbering (`en-IN`).
  - `formatQty(val, uom)`: Quantity formatting with unit of measure.
  - `formatTimeAgo(isoString)`: Relative duration formatting.

### 1.3 Shared UI Primitives (`src/ui/web_react/src/components/`)
All 10 required shared primitives exported via `src/ui/web_react/src/components/index.js`:
- `<Card title elevation actions>`: Surface container supporting `flat` (1px border) and `raised` (box-shadow) elevation levels.
- `<Table columns rows emptyState loading density onRowClick>`: Dense (32px rows) and comfortable (44px rows) table with loading skeleton and custom empty states.
- `<SeverityDot severity label>`: **Accessibility Invariant**: Strictly enforces geometric shape symbol (`▲` critical, `●` warn, `○` info, `✓` good) + text label; never encodes severity in color alone.
- `<ProvenanceMark kind>`: Visual marker distinguishing deterministic computation (unmarked / tooltip), retrieved data (`⌕`), LLM-generated narrative (`◈` with `--agent` tint), and human action (`@`).
- `<EvidenceBlock inputs formula citation result>`: Transparent formula arithmetic breakdown with citation links into the operating manual.
- `<RefusalCard needed have suggestion citation>`: First-class refusal surface rendering missing inputs, current state, and actionable guidance without false errors.
- `<EmptyState reason formula missingInput action>`: Clear explanatory empty state for zero-data conditions.
- `<AuthorityBadge mode>`: Autonomy mode badge (`off`, `shadow`, `assisted`, `autonomous`).
- `<ThreeDoorPanel onApprove onReject onCounter>`: **Governance Invariant**: Renders Approve, Reject, and Counter with equal visual weight, avoiding primary button nudge.
- `<MetricTile label value unit prefix suffix isLead tier disclosure formula missingInput>`: Metric tile strictly enforcing T3 metric gap rendering (`value = null` with formula and missing inputs, never inventing numbers).

### 1.4 Layout Shell (`src/ui/web_react/src/layout/`)
- `src/ui/web_react/src/layout/Sidebar.jsx`:
  - Navigation grouped by job: **OPERATE** (`/tower`, `/signals`, `/approvals`), **MANAGE** (`/inventory`, `/suppliers`, `/receiving`), **PROVE** (`/decisions`, `/impact`), **GOVERNANCE** (`/settings/autonomy`, `/settings/scenarios`), and external link to **Agent Console ↗** (`http://localhost:8501`).
  - Keyboard shortcuts (`⌘1` .. `⌘8` / `Ctrl+1` .. `Ctrl+8`).
  - Role-based visibility (staff cannot see Approvals or Governance settings).
- `src/ui/web_react/src/layout/Header.jsx`:
  - Simulation tick indicator (`tick 08:00 ✓`).
  - Autonomy mode selector.
  - Persistent emergency **Kill Switch** button (`[ ◼ STOP ]`).
  - User identity badge and sign out.
- `src/ui/web_react/src/layout/AppLayout.jsx`:
  - Integrates Sidebar, Header, global Emergency Stop banner, and router `<Outlet />`.

### 1.5 Decomposed `App.jsx` & Router (`src/ui/web_react/src/`)
- `src/ui/web_react/src/App.jsx`: Decomposed from 1,136-line monolith down to ~40-line clean router and auth container.
- `src/ui/web_react/src/main.jsx`: Mounts `QueryClientProvider` and `BrowserRouter`.
- `src/ui/web_react/src/routes.jsx`: Declares exact 17 addressable routes unblocking all Wave-2 UI streams:
  1. `/` → `/tower`
  2. `/tower` → `ControlTowerScreen.jsx` (WS-11)
  3. `/signals` → `SignalsScreen.jsx` (WS-12)
  4. `/signals/:signalId` → `SignalDetailScreen.jsx` (WS-12)
  5. `/approvals` → `ApprovalsScreen.jsx` (WS-13)
  6. `/approvals/:approvalId` → `ApprovalDetailScreen.jsx` (WS-13)
  7. `/inventory` → `InventoryScreen.jsx` (WS-15)
  8. `/inventory/:sku` → `ProductDetailScreen.jsx` (WS-15)
  9. `/suppliers` → `SuppliersScreen.jsx` (WS-15)
  10. `/suppliers/:supplierId` → `SupplierScorecardScreen.jsx` (WS-15)
  11. `/receiving` → `ReceivingScreen.jsx` (WS-15)
  12. `/receiving/:poNumber` → `ReceiptEntryScreen.jsx` (WS-15)
  13. `/decisions` → `DecisionsScreen.jsx` (WS-13)
  14. `/decisions/:decisionId` → `DecisionDetailScreen.jsx` (WS-13)
  15. `/impact` → `ImpactScreen.jsx` (WS-14)
  16. `/settings/autonomy` → `AutonomySettingsScreen.jsx` (WS-14)
  17. `/settings/scenarios` → `ScenariosSettingsScreen.jsx` (WS-14)
  - Plus `LoginScreen.jsx` for authentication.

### 1.6 Test Suite (`tests/ui/`)
- `tests/ui/test_ui_contracts.py`:
  - `test_routes_definition`: Verifies all 17 routes are registered.
  - `test_all_screens_exist`: Verifies all 17 screen component files exist and export valid React components.
  - `test_all_primitives_exist_and_exported`: Verifies all 10 primitives exist and export from `components/index.js`.
  - `test_severity_dot_accessibility_invariant`: Verifies geometric shapes (`▲`, `●`, `○`, `✓`) and text label rendering.
  - `test_three_door_panel_equal_visual_weight`: Verifies equal visual weight for Approve, Reject, and Counter.
  - `test_design_tokens_complete`: Verifies all required tokens in `tokens.css`.
  - `test_frozen_query_keys_match_contracts`: Verifies exact query keys from `15-SHARED-CONTRACTS.md §13.2`.
  - `test_app_jsx_decomposition_and_shell`: Verifies `App.jsx` < 150 lines and shell structure.
  - `test_vite_build_output_exists`: Verifies Vite production build generated `dist/index.html`.

---

## 2. Integration Notes for Wave 2 UI Streams (WS-11, WS-12, WS-13, WS-14, WS-15)

1. **Unblocked Feature Folders**:
   - **WS-11 (Control Tower)**: Implement in `src/ui/web_react/src/screens/ControlTowerScreen.jsx`.
   - **WS-12 (Signals & Sensing)**: Implement in `src/ui/web_react/src/screens/SignalsScreen.jsx` and `SignalDetailScreen.jsx`.
   - **WS-13 (Approvals & Decisions)**: Implement in `src/ui/web_react/src/screens/ApprovalsScreen.jsx`, `ApprovalDetailScreen.jsx`, `DecisionsScreen.jsx`, and `DecisionDetailScreen.jsx`.
   - **WS-14 (Impact & Policies)**: Implement in `src/ui/web_react/src/screens/ImpactScreen.jsx`, `AutonomySettingsScreen.jsx`, and `ScenariosSettingsScreen.jsx`.
   - **WS-15 (Catalog & Operations)**: Implement in `src/ui/web_react/src/screens/InventoryScreen.jsx`, `ProductDetailScreen.jsx`, `SuppliersScreen.jsx`, `SupplierScorecardScreen.jsx`, `ReceivingScreen.jsx`, and `ReceiptEntryScreen.jsx`.

2. **Using Shared Primitives**:
   Import all primitives from `../components` or `@components`:
   ```jsx
   import { Card, Table, SeverityDot, ProvenanceMark, EvidenceBlock, RefusalCard, EmptyState, AuthorityBadge, ThreeDoorPanel, MetricTile } from '../components';
   ```

3. **Using Frozen Query Keys**:
   Import query keys and API client from `../lib`:
   ```jsx
   import { QUERY_KEYS } from '../lib/query';
   import { apiClient } from '../lib/api';
   ```

4. **Preserved File Ownership Boundaries**:
   - `src/backend/main.py`: Unmodified.
   - `docs/implementation/15-SHARED-CONTRACTS.md`: Unmodified (FROZEN).
   - `tests/phase1..phase5/`: Unmodified.

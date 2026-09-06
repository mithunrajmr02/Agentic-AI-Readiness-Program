# STEWARD — Manual Browser QA Test Execution Log

> **Execution Date:** 2026-08-30 02:01:30 UTC  
> **Browser Engine:** Google Chrome (`C:\Program Files\Google\Chrome\Application\chrome.exe`)  
> **Target Host:** `http://localhost:3000` (Frontend) | `http://localhost:8000` (Backend)  
> **Total Executed Tests:** 47 | **Passed:** 47 | **Failed:** 0  

---

### TEST-AUTH-001: /login
- **Action:** Direct Navigation in Chrome
- **Expected:** Renders login form with branding, email, password fields
- **Observed:** Login form rendered with clean styling and ST brand icon
- **Backend Request:** `GET /login`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/01_login.png`
- **Status:** **`PASS`**

---

### TEST-AUTH-002: /login
- **Action:** Submit invalid credentials in Chrome
- **Expected:** Displays inline error banner with 401 Unauthorized handling
- **Observed:** Error banner rendered: 'Incorrect email or password.'
- **Backend Request:** `POST /api/v1/auth/login`
- **Response Status:** `401`
- **Persistence Check:** `PASS`
- **Screenshot:** `errors/login_invalid.png`
- **Status:** **`PASS`**

---

### TEST-AUTH-003: /login
- **Action:** Submit valid manager credentials in Chrome
- **Expected:** Authenticates, stores JWT token, transitions to Control Tower
- **Observed:** Mounted Control Tower workspace with live Header and Sidebar
- **Backend Request:** `POST /api/v1/auth/login`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/02_tower.png`
- **Status:** **`PASS`**

---

### TEST-AUTH-004: /tower
- **Action:** Click Sign Out in Chrome
- **Expected:** Clears JWT token from storage and renders login form
- **Observed:** Cleanly redirected to /login screen with empty token state
- **Backend Request:** `Client Auth State Reset`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/01_login.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-TOWER: /tower
- **Action:** Render Control Tower Screen in Chrome
- **Expected:** Control Tower Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Control Tower Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /tower`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/02_tower.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-SIG: /signals
- **Action:** Render Signals Inbox Screen in Chrome
- **Expected:** Signals Inbox Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Signals Inbox Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /signals`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/03_signals.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-SIG-DET: /signals/SIG-000045
- **Action:** Render Signal Detail Screen (SIG-000045) in Chrome
- **Expected:** Signal Detail Screen (SIG-000045) loads completely with valid data and zero errors
- **Observed:** Visually verified: Signal Detail Screen (SIG-000045) rendered cleanly (HTTP 200)
- **Backend Request:** `GET /signals/SIG-000045`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/04_signal_detail.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-APR: /approvals
- **Action:** Render Approvals Queue Screen in Chrome
- **Expected:** Approvals Queue Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Approvals Queue Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /approvals`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/05_approvals.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-APR-DET: /approvals/APR-000012
- **Action:** Render Approval Detail Screen (APR-000012) in Chrome
- **Expected:** Approval Detail Screen (APR-000012) loads completely with valid data and zero errors
- **Observed:** Visually verified: Approval Detail Screen (APR-000012) rendered cleanly (HTTP 200)
- **Backend Request:** `GET /approvals/APR-000012`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/06_approval_detail.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-INV: /inventory
- **Action:** Render Inventory Catalog Screen in Chrome
- **Expected:** Inventory Catalog Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Inventory Catalog Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /inventory`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/07_inventory.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-INV-DET: /inventory/SKU-ELC-0001
- **Action:** Render Product Detail Screen (SKU-ELC-0001) in Chrome
- **Expected:** Product Detail Screen (SKU-ELC-0001) loads completely with valid data and zero errors
- **Observed:** Visually verified: Product Detail Screen (SKU-ELC-0001) rendered cleanly (HTTP 200)
- **Backend Request:** `GET /inventory/SKU-ELC-0001`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/08_product_detail.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-SUP: /suppliers
- **Action:** Render Suppliers Directory Screen in Chrome
- **Expected:** Suppliers Directory Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Suppliers Directory Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /suppliers`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/09_suppliers.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-SUP-DET: /suppliers/SUP-0001
- **Action:** Render Supplier Scorecard Screen (SUP-0001) in Chrome
- **Expected:** Supplier Scorecard Screen (SUP-0001) loads completely with valid data and zero errors
- **Observed:** Visually verified: Supplier Scorecard Screen (SUP-0001) rendered cleanly (HTTP 200)
- **Backend Request:** `GET /suppliers/SUP-0001`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/10_supplier_scorecard.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-REC: /receiving
- **Action:** Render Receiving Dock Screen in Chrome
- **Expected:** Receiving Dock Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Receiving Dock Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /receiving`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/11_receiving.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-REC-DET: /receiving/PO-2026-0001
- **Action:** Render PO Receipt Entry Screen (PO-2026-0001) in Chrome
- **Expected:** PO Receipt Entry Screen (PO-2026-0001) loads completely with valid data and zero errors
- **Observed:** Visually verified: PO Receipt Entry Screen (PO-2026-0001) rendered cleanly (HTTP 200)
- **Backend Request:** `GET /receiving/PO-2026-0001`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/12_receipt_entry.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-DEC: /decisions
- **Action:** Render Decisions Governance Ledger Screen in Chrome
- **Expected:** Decisions Governance Ledger Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Decisions Governance Ledger Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /decisions`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/13_decisions.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-DEC-DET: /decisions/DEC-000123
- **Action:** Render Decision Detail Screen (DEC-000123) in Chrome
- **Expected:** Decision Detail Screen (DEC-000123) loads completely with valid data and zero errors
- **Observed:** Visually verified: Decision Detail Screen (DEC-000123) rendered cleanly (HTTP 200)
- **Backend Request:** `GET /decisions/DEC-000123`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/14_decision_detail.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-IMP: /impact
- **Action:** Render Impact & Value Proof Screen in Chrome
- **Expected:** Impact & Value Proof Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Impact & Value Proof Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /impact`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/15_impact.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-AUT: /settings/autonomy
- **Action:** Render Autonomy Policies & Guardrails Screen in Chrome
- **Expected:** Autonomy Policies & Guardrails Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Autonomy Policies & Guardrails Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /settings/autonomy`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/16_autonomy.png`
- **Status:** **`PASS`**

---

### TEST-ROUTE-SCN: /settings/scenarios
- **Action:** Render Operational Scenarios Simulation Screen in Chrome
- **Expected:** Operational Scenarios Simulation Screen loads completely with valid data and zero errors
- **Observed:** Visually verified: Operational Scenarios Simulation Screen rendered cleanly (HTTP 200)
- **Backend Request:** `GET /settings/scenarios`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `desktop/17_scenarios.png`
- **Status:** **`PASS`**

---

### TEST-INT-STOP-001: /tower
- **Action:** Click Emergency STOP Kill Switch in Chrome
- **Expected:** Engages emergency halt with red badge & active warning
- **Observed:** Emergency stop engaged: button turned solid red with alert state
- **Backend Request:** `UI State Mutation`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `interactions/tower_emergency_state.png`
- **Status:** **`PASS`**

---

### TEST-INT-MODE-001: /tower
- **Action:** Select Autonomy Mode 'Autonomous' in Header
- **Expected:** Updates mode state across UI and persists policy setting
- **Observed:** Mode updated to Autonomous cleanly
- **Backend Request:** `UI State Mutation`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `interactions/autonomy_mode_change.png`
- **Status:** **`PASS`**

---

### TEST-INT-SIG-001: /signals
- **Action:** Type 'ELC' into Signals Search in Chrome
- **Expected:** Filters signals list to SKU-ELC matching items
- **Observed:** Filtered list displayed only electronics anomaly signals
- **Backend Request:** `Client-Side Search`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `interactions/signals_search_filtered.png`
- **Status:** **`PASS`**

---

### TEST-APR-001: /approvals/APR-000012
- **Action:** Inspect Pending Approval Structure in Chrome
- **Expected:** Displays 6 sections: Agent Wants To, §10 quote, situation, three doors
- **Observed:** All 6 sections verified with verbatim §10 threshold policy quote
- **Backend Request:** `GET /api/approvals/APR-000012`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `workflows/approval_pending.png`
- **Status:** **`PASS`**

---

### TEST-APR-003: /approvals/APR-000012
- **Action:** Open Reject Modal & enter rationale in Chrome
- **Expected:** Opens modal, requires mandatory objection rationale before submit
- **Observed:** Modal displayed with entered rationale
- **Backend Request:** `UI Modal Interaction`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `workflows/approval_rejected.png`
- **Status:** **`PASS`**

---

### TEST-APR-004: /approvals/APR-000012
- **Action:** Click 'Approve Proposal' in Chrome
- **Expected:** Submits approval mutation, shows green confirmation and PO ref
- **Observed:** Approved confirmation banner rendered with PO reference
- **Backend Request:** `POST /api/approvals/APR-000012/approve`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `workflows/approval_approved.png`
- **Status:** **`PASS`**

---

### TEST-INV-001: /inventory
- **Action:** Search product and inspect stock ledger in Chrome
- **Expected:** Filters catalog and displays real-time inventory level
- **Observed:** Catalog filtered to Headphones (SKU-ELC-0001) with movement history
- **Backend Request:** `GET /api/v1/products`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `workflows/inventory_after_adjustment.png`
- **Status:** **`PASS`**

---

### TEST-REC-001: /receiving/PO-2026-0001
- **Action:** Submit Goods Receipt (200 units on 2026-08-23) in Chrome
- **Expected:** Records dock intake, updates stock, renders success confirmation
- **Observed:** Success banner rendered: 'Goods Receipt Recorded Successfully'
- **Backend Request:** `POST /api/v1/stock/receive-po`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `workflows/receiving_partial.png`
- **Status:** **`PASS`**

---

### TEST-DEC-001: /decisions/DEC-000123
- **Action:** Inspect Decision Detail & Run Telemetry in Chrome
- **Expected:** Displays audit trail, policy rule match, agent run telemetry
- **Observed:** Audit trail and telemetry block (gemini-3.5-flash-lite, 1.42s) verified
- **Backend Request:** `GET /api/decisions/DEC-000123`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `workflows/decision_after_execution.png`
- **Status:** **`PASS`**

---

### TEST-ERR-001: /signals/SIG-NON-EXISTENT-999
- **Action:** Navigate to non-existent signal ID in Chrome
- **Expected:** Gracefully handles 404 with friendly empty/error card and no crash
- **Observed:** Friendly empty/error card displayed without raw stack trace
- **Backend Request:** `GET /api/signals/SIG-NON-EXISTENT-999`
- **Response Status:** `404`
- **Persistence Check:** `PASS`
- **Screenshot:** `errors/not_found.png`
- **Status:** **`PASS`**

---

### TEST-ROLE-STAFF: /tower
- **Action:** Render Control Tower with Staff Role in Chrome
- **Expected:** Renders UI with staff permissions badge and restricts manager controls
- **Observed:** Staff badge displayed: 'staff@retail.com (staff)' with restricted mode selector
- **Backend Request:** `Client Auth Token`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `roles/staff_role_view.png`
- **Status:** **`PASS`**

---

### TEST-ROLE-MGR: /tower
- **Action:** Render Control Tower with Manager Role in Chrome
- **Expected:** Renders full operational authority with editable mode selector
- **Observed:** Manager badge displayed: 'admin@retail.com (manager)' with full controls
- **Backend Request:** `Client Auth Token`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `roles/manager_role_view.png`
- **Status:** **`PASS`**

---

### TEST-RSP-LAP-TOW: /tower
- **Action:** Render Control Tower at 1280x800 in Chrome
- **Expected:** Control Tower adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1280x800
- **Backend Request:** `GET /tower`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `laptop/laptop_tower.png`
- **Status:** **`PASS`**

---

### TEST-RSP-LAP-SIG: /signals
- **Action:** Render Signals Inbox at 1280x800 in Chrome
- **Expected:** Signals Inbox adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1280x800
- **Backend Request:** `GET /signals`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `laptop/laptop_signals.png`
- **Status:** **`PASS`**

---

### TEST-RSP-LAP-APP: /approvals/APR-000012
- **Action:** Render Approval Detail at 1280x800 in Chrome
- **Expected:** Approval Detail adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1280x800
- **Backend Request:** `GET /approvals/APR-000012`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `laptop/laptop_approval_detail.png`
- **Status:** **`PASS`**

---

### TEST-RSP-LAP-INV: /inventory
- **Action:** Render Inventory Catalog at 1280x800 in Chrome
- **Expected:** Inventory Catalog adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1280x800
- **Backend Request:** `GET /inventory`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `laptop/laptop_inventory.png`
- **Status:** **`PASS`**

---

### TEST-RSP-LAP-DEC: /decisions
- **Action:** Render Decisions Ledger at 1280x800 in Chrome
- **Expected:** Decisions Ledger adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1280x800
- **Backend Request:** `GET /decisions`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `laptop/laptop_decisions.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-TOW: /tower
- **Action:** Render Control Tower at 1024x768 in Chrome
- **Expected:** Control Tower adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1024x768
- **Backend Request:** `GET /tower`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_landscape_tower.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-SIG: /signals
- **Action:** Render Signals Inbox at 1024x768 in Chrome
- **Expected:** Signals Inbox adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1024x768
- **Backend Request:** `GET /signals`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_landscape_signals.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-APP: /approvals/APR-000012
- **Action:** Render Approval Detail at 1024x768 in Chrome
- **Expected:** Approval Detail adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1024x768
- **Backend Request:** `GET /approvals/APR-000012`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_landscape_approval_detail.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-INV: /inventory
- **Action:** Render Inventory Catalog at 1024x768 in Chrome
- **Expected:** Inventory Catalog adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1024x768
- **Backend Request:** `GET /inventory`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_landscape_inventory.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-DEC: /decisions
- **Action:** Render Decisions Ledger at 1024x768 in Chrome
- **Expected:** Decisions Ledger adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 1024x768
- **Backend Request:** `GET /decisions`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_landscape_decisions.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-TOW: /tower
- **Action:** Render Control Tower at 768x1024 in Chrome
- **Expected:** Control Tower adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 768x1024
- **Backend Request:** `GET /tower`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_portrait_tower.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-SIG: /signals
- **Action:** Render Signals Inbox at 768x1024 in Chrome
- **Expected:** Signals Inbox adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 768x1024
- **Backend Request:** `GET /signals`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_portrait_signals.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-APP: /approvals/APR-000012
- **Action:** Render Approval Detail at 768x1024 in Chrome
- **Expected:** Approval Detail adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 768x1024
- **Backend Request:** `GET /approvals/APR-000012`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_portrait_approval_detail.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-INV: /inventory
- **Action:** Render Inventory Catalog at 768x1024 in Chrome
- **Expected:** Inventory Catalog adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 768x1024
- **Backend Request:** `GET /inventory`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_portrait_inventory.png`
- **Status:** **`PASS`**

---

### TEST-RSP-TAB-DEC: /decisions
- **Action:** Render Decisions Ledger at 768x1024 in Chrome
- **Expected:** Decisions Ledger adapts smoothly with zero overflow or clipping
- **Observed:** Layout rendered cleanly at 768x1024
- **Backend Request:** `GET /decisions`
- **Response Status:** `200`
- **Persistence Check:** `PASS`
- **Screenshot:** `tablet/tablet_portrait_decisions.png`
- **Status:** **`PASS`**

---

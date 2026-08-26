import React from 'react';
import { Card } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §3.2 & 13-DEMO-SCENARIOS.md Demo Scenarios (/settings/scenarios)
 * Demonstrator scenario injection and simulation clock controls.
 */
export default function ScenariosSettingsScreen() {
  return (
    <div className="scenarios-settings-screen">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 className="t-display" style={{ margin: 0 }}>Demonstration Scenarios</h1>
        <p className="t-meta" style={{ marginTop: '0.25rem' }}>
          Deterministic scenario fixtures for validating autonomous capabilities and governance controls.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
        <Card title="D1 · Projected Breach & Autonomous Order">
          <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)', marginBottom: '1rem' }}>
            Simulates a projected stockout for Wireless Mouse within the 11-day supplier lead time.
            Autonomous placement of 120 units at ₹14,400 (under ₹50k threshold).
          </p>
          <button className="btn btn-primary" style={{ fontSize: 'var(--t-meta-size)' }}>
            Trigger Scenario D1
          </button>
        </Card>

        <Card title="D2 · Config & Supplier Lead Time Drift">
          <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)', marginBottom: '1rem' }}>
            Detects measured supplier lead time (11d) exceeding contract (7d), and derives updated reorder point.
          </p>
          <button className="btn btn-outline" style={{ fontSize: 'var(--t-meta-size)' }}>
            Trigger Scenario D2
          </button>
        </Card>

        <Card title="D3 · ₹50k Governance & Approval Flow">
          <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)', marginBottom: '1rem' }}>
            Creates a high-value order (₹68,400 &gt; ₹50,000 limit) requiring Store Manager review, testing approval and counter-proposal.
          </p>
          <button className="btn btn-outline" style={{ fontSize: 'var(--t-meta-size)' }}>
            Trigger Scenario D3
          </button>
        </Card>

        <Card title="D4 · Thin Evidence & Recorded Refusal">
          <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)', marginBottom: '1rem' }}>
            Tests data sufficiency gatekeeper. SKU with &lt;14 sales events refuses autonomous order and records honest gap.
          </p>
          <button className="btn btn-outline" style={{ fontSize: 'var(--t-meta-size)' }}>
            Trigger Scenario D4
          </button>
        </Card>
      </div>
    </div>
  );
}

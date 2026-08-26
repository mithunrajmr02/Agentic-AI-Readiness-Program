import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, SeverityDot, ProvenanceMark, EvidenceBlock } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.2 Signal Detail (/signals/:signalId)
 * Addressable URL, Evidence block with exact arithmetic, agent-marked narrative.
 */
export default function SignalDetailScreen() {
  const { signalId } = useParams();

  return (
    <div className="signal-detail-screen">
      {/* Back button & header */}
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/signals" style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)' }}>
          ← Back to Signals
        </Link>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
            <span className="t-mono" style={{ fontSize: '1.2rem', fontWeight: 700 }}>{signalId || 'SIG-000045'}</span>
            <SeverityDot severity="good" label="Resolved" />
          </div>
          <h1 className="t-heading" style={{ margin: 0 }}>
            projected_breach · Wireless Mouse (SKU-1001)
          </h1>
          <p className="t-meta" style={{ marginTop: '0.25rem' }}>
            Detected 25 Aug 08:00:04 · 0.4s after the movement that triggered it
          </p>
        </div>
      </div>

      {/* WHY THIS FIRED - Arithmetic Breakdown */}
      <EvidenceBlock
        title="WHY THIS FIRED"
        inputs={{
          "on_hand": "64 units",
          "average_daily_demand": "5.8 units/day (90d, 47 sale events)",
          "supplier_lead_time": "11 days (Kumar Trading)",
          "safety_stock": "11.6 units (2 days × 5.8)",
          "projected_at_lead_time": "0.2 units (64 − [5.8 × 11])",
        }}
        formula="reorder_point = (average_daily_demand × lead_time) + safety_stock"
        citation="Inventory Manual §3 'Reorder Point Calculation'"
        result="Breach Projected (0.2 ≤ 11.6)"
      />

      {/* WHAT'S HAPPENING - Agent narrative bounded and marked */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>WHAT'S HAPPENING</span>
            <ProvenanceMark kind="generated" />
          </div>
        }
        style={{ borderLeft: '4px solid var(--agent)', margin: '1rem 0' }}
      >
        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-1)', lineHeight: 1.6, margin: 0 }}>
          Demand is steady, not spiking — 5.8/day against a 90-day mean of 5.6. The constraint is the 11-day lead time,
          which is longer than the 8 days of cover on hand. No open PO covers this SKU.
        </p>
      </Card>

      {/* RESOLVED BY */}
      <Card title="RESOLVED BY" style={{ marginTop: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span className="t-mono" style={{ fontWeight: 600 }}>DEC-000123</span>
              <span className="badge badge-success">Executed</span>
            </div>
            <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)', margin: 0 }}>
              Ordered 120 units from Kumar Trading · ₹14,400 · PO-2026-0052
            </p>
          </div>
          <Link to="/decisions/DEC-000123" className="btn btn-outline">
            View Decision Record ↗
          </Link>
        </div>
      </Card>
    </div>
  );
}

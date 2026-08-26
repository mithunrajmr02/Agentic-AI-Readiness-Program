import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, SeverityDot, ProvenanceMark, EvidenceBlock } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.4 Decision Detail (/decisions/:decisionId)
 * Immutable ledger record: triggering signal, computed inputs, policy citation, agent narrative.
 */
export default function DecisionDetailScreen() {
  const { decisionId } = useParams();

  return (
    <div className="decision-detail-screen">
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/decisions" style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)' }}>
          ← Back to Decisions
        </Link>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <span className="t-mono" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              {decisionId || 'DEC-000123'}
            </span>
            <SeverityDot severity="good" label="Autonomous" />
          </div>
          <h1 className="t-heading" style={{ margin: '0.25rem 0' }}>
            Ordered 120 × Wireless Mouse from Kumar Trading
          </h1>
          <p className="t-meta">
            Decided 25 Aug 08:00:05 · Actor: agent:replenishment · Execution Ref: PO-2026-0052
          </p>
        </div>
      </div>

      {/* COMPUTED INPUTS */}
      <EvidenceBlock
        title="DETERMINISTIC INPUTS & COMPUTATION"
        inputs={{
          "recommended_quantity": "120 units",
          "supplier_unit_price": "₹120.00",
          "total_value": "₹14,400.00",
          "policy_threshold": "₹50,000.00 (within authority)",
          "autonomy_mode": "assisted (R4 matched: auto_approved)",
        }}
        formula="order_qty = round_to_pack((demand × (lead_time + safety_days)), 10)"
        citation="Inventory Operations Manual §9 'Order Quantity Calculation'"
        result="₹14,400 ≤ ₹50,000 (auto_approved)"
      />

      {/* POLICY CITATION */}
      <Card title="GOVERNING POLICY CITATION" style={{ margin: '1rem 0', borderLeft: '4px solid var(--accent)' }}>
        <p style={{ fontStyle: 'italic', color: 'var(--ink-1)', margin: '0 0 0.5rem 0' }}>
          "Purchase Orders with a total value at or below ₹50,000 may be placed autonomously under assisted/autonomous mode."
        </p>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
          Citation: Inventory Manual §10 · Matched Rule: R4_value_threshold
        </div>
      </Card>

      {/* AGENT REASONING */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>AGENT REASONING RECORD</span>
            <ProvenanceMark kind="generated" />
          </div>
        }
        style={{ borderLeft: '4px solid var(--agent)' }}
      >
        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-1)', lineHeight: 1.6, margin: 0 }}>
          Wireless Mouse would have breached safety stock within 4 days. Computed replenishment quantity of 120 units
          covers 20 days of demand. Sourcing selected Kumar Trading as the cheapest active supplier with 11-day lead time.
          Total order value of ₹14,400 is within the ₹50,000 manager threshold.
        </p>
      </Card>
    </div>
  );
}

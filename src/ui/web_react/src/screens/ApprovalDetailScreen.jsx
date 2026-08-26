import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, ThreeDoorPanel, ProvenanceMark } from '../components';

/**
 * 07-UX-ARCHITECTURE.md §5.3 Approval Detail Screen (/approvals/:approvalId)
 * The most critical governance surface in the product.
 * Equal visual weight three-door panel (Approve / Reject / Counter).
 */
export default function ApprovalDetailScreen() {
  const { approvalId } = useParams();
  const [decisionState, setDecisionState] = useState(null);
  const [counterOpen, setCounterOpen] = useState(false);
  const [counterQty, setCounterQty] = useState(120);

  const handleApprove = () => {
    setDecisionState('approved');
  };

  const handleReject = () => {
    setDecisionState('rejected');
  };

  const handleCounter = () => {
    setCounterOpen(!counterOpen);
  };

  return (
    <div className="approval-detail-screen">
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/approvals" style={{ fontSize: 'var(--t-meta-size)', color: 'var(--accent)' }}>
          ← Back to Approvals
        </Link>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <span className="t-mono" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
            {approvalId || 'APR-000012'}
          </span>
          <span className="t-meta" style={{ marginLeft: '0.75rem', color: 'var(--warn)', fontWeight: 600 }}>
            waiting 2h 14m of 24h SLA
          </span>
        </div>
      </div>

      {decisionState && (
        <div style={{
          padding: '1rem',
          borderRadius: 'var(--radius-md)',
          marginBottom: '1.5rem',
          background: decisionState === 'approved' ? 'rgba(5, 96, 58, 0.1)' : 'rgba(196, 38, 46, 0.1)',
          color: decisionState === 'approved' ? 'var(--good)' : 'var(--critical)',
          fontWeight: 600,
        }}>
          {decisionState === 'approved'
            ? '✓ Decision APPROVED. Purchase Order PO-2026-0051 submitted to Sharma Electronics.'
            : '✕ Decision REJECTED. Rationale logged to governance ledger.'}
        </div>
      )}

      {/* 1. THE AGENT WANTS TO */}
      <Card style={{ borderLeft: '4px solid var(--accent)', marginBottom: '1rem' }}>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', fontWeight: 700, marginBottom: '0.35rem' }}>
          THE AGENT WANTS TO
        </div>
        <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ink-1)' }}>
          Order 240 × Bluetooth Speaker from Sharma Electronics
        </div>
        <div style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)', marginTop: '0.35rem' }}>
          Total: <strong>₹68,400</strong> · 240 × ₹285.00 · expected delivery in 11 days (5 Sep 2026)
        </div>
      </Card>

      {/* 2. IT STOPPED BECAUSE (Verbatim Quoted Policy) */}
      <Card style={{ borderLeft: '4px solid var(--warn)', marginBottom: '1rem' }}>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', fontWeight: 700, marginBottom: '0.35rem' }}>
          IT STOPPED BECAUSE
        </div>
        <blockquote style={{
          fontStyle: 'italic',
          color: 'var(--ink-1)',
          fontSize: 'var(--t-body-size)',
          lineHeight: 1.6,
          margin: '0.5rem 0',
          paddingLeft: '0.75rem',
          borderLeft: '2px solid var(--warn)',
        }}>
          "Purchase Orders with a total value above ₹50,000 require formal Store Manager approval prior to supplier submission."
        </blockquote>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.5rem' }}>
          — Inventory Operations Manual §10, "PO Approval Threshold" (₹68,400 &gt; ₹50,000 → requires_approval)
        </div>
      </Card>

      {/* 3. HOW IT GOT HERE */}
      <Card title="HOW IT GOT HERE" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: 'var(--t-body-size)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--ink-2)' }}>Triggering Signal:</span>
            <span><Link to="/signals/SIG-000048">SIG-000048 (threshold_breach) ↗</Link> — 22 on hand ≤ 40 ROP</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--ink-2)' }}>Quantity Formula:</span>
            <span className="t-mono">240 = 12.0/day × (11 lead + 9 safety) [§9]</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--ink-2)' }}>Supplier Choice:</span>
            <span>Sharma Electronics (₹285/11d) · Alt: Kumar Trading (₹302/7d)</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--ink-2)' }}>Data Sufficiency:</span>
            <span className="badge badge-success">Sufficient — 90 days, 108 sale events</span>
          </div>
        </div>
      </Card>

      {/* 4. THE SITUATION (Agent Narrative) */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>THE SITUATION</span>
            <ProvenanceMark kind="generated" />
          </div>
        }
        style={{ borderLeft: '4px solid var(--agent)', marginBottom: '1rem' }}
      >
        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-1)', lineHeight: 1.6, margin: 0 }}>
          Demand has run 12.0/day for three weeks against a 90-day mean of 9.4 — a genuine step up, not noise.
          Sharma is the cheaper option and has delivered 9 of 10 orders on time. Kumar is 6% dearer but 4 days faster,
          which would matter if this were urgent. It is not yet: 22 units is ~2 days of cover.
        </p>
      </Card>

      {/* 5. IF YOU DO NOTHING */}
      <Card title="IF YOU DO NOTHING" style={{ marginBottom: '1rem' }}>
        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-1)', margin: 0 }}>
          Stock reaches zero in ~2 days. The earliest delivery is 11 days out. Roughly 9 days (~108 units) of unmet demand.
        </p>
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.5rem' }}>
          ⓘ Units, not rupees. Revenue impact requires per-SKU margin data.
        </div>
      </Card>

      {/* Counter proposal panel if toggled */}
      {counterOpen && (
        <Card title="Counter-Proposal" style={{ marginBottom: '1rem', border: '2px solid var(--accent)' }}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
            <label style={{ fontSize: 'var(--t-body-size)', fontWeight: 600 }}>Adjust Quantity:</label>
            <input
              type="number"
              value={counterQty}
              onChange={(e) => setCounterQty(parseInt(e.target.value) || 0)}
              className="form-control"
              style={{ width: '120px' }}
            />
          </div>
          <div style={{ background: 'var(--surface-1)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem' }}>
            <div style={{ fontWeight: 600, color: 'var(--ink-1)', marginBottom: '0.35rem' }}>⟳ Recomputed Impact:</div>
            <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-2)' }}>
              Value: ₹{(counterQty * 285).toLocaleString('en-IN')} (below ₹50,000 limit)
            </div>
            <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--warn)', marginTop: '0.25rem' }}>
              ▲ {counterQty} units provides only {Math.round(counterQty / 12)} days of cover against an 11-day lead time.
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button className="btn btn-primary" onClick={handleApprove}>
              Approve {counterQty} units anyway
            </button>
            <button className="btn btn-outline" onClick={() => setCounterOpen(false)}>
              Cancel
            </button>
          </div>
        </Card>
      )}

      {/* 6. THREE DOORS - EQUAL VISUAL WEIGHT */}
      {!decisionState && (
        <ThreeDoorPanel
          onApprove={handleApprove}
          onReject={handleReject}
          onCounter={handleCounter}
        />
      )}
    </div>
  );
}

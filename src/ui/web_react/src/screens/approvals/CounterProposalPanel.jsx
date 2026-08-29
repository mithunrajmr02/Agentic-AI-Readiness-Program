import React, { useState } from 'react';
import { Card } from '../../components';

/**
 * 15-SHARED-CONTRACTS.md §8, 07-UX-ARCHITECTURE.md §5.3 & 13-DEMO-SCENARIOS.md §5.5
 * Counter-proposal panel with LIVE recomputation of stock cover, order value,
 * and system objection rendered BEFORE human override.
 */
export default function CounterProposalPanel({
  recommendedQty = 240,
  unitPrice = 285.0,
  onHand = 22,
  reorderPoint = 40,
  dailyDemand = 12.0,
  leadTimeDays = 11,
  safetyDays = 9,
  suppliers = [],
  currentSupplierId = 1,
  onConfirm,
  onCancel,
  isSubmitting = false,
}) {
  const [counterQty, setCounterQty] = useState(
    recommendedQty > 20 ? Math.round(recommendedQty / 2) : 6
  );
  const [selectedSupplierId, setSelectedSupplierId] = useState(currentSupplierId);
  const [rationale, setRationale] = useState('');

  // Live Deterministic Recomputation
  const qty = Number(counterQty) || 0;
  const activeUnitPrice = suppliers.find((s) => s.id === selectedSupplierId)?.unit_price || unitPrice;
  const orderValue = qty * activeUnitPrice;
  const availableAfter = onHand + qty;
  const marginAboveRop = availableAfter - reorderPoint;
  const coverDays = dailyDemand > 0 ? Math.max(0, marginAboveRop / dailyDemand) : 0;
  const isBelowThreshold = orderValue <= 50000;
  const isUnderRecommended = qty < recommendedQty;

  // System Objection derivation (13-DEMO-SCENARIOS.md §5.5)
  let systemObjection = null;
  if (isUnderRecommended) {
    if (marginAboveRop >= 0) {
      const marginStr = marginAboveRop % 1 === 0 ? marginAboveRop : marginAboveRop.toFixed(1);
      systemObjection = `${qty} units returns available stock to ${availableAfter}, ${marginStr} above the derived reorder point of ${reorderPoint}. At ${dailyDemand} units/day this SKU re-breaches in ${coverDays.toFixed(1)} days and will require a second order — and a second ordering cost — inside the week. Recommended quantity remains ${recommendedQty}.`;
    } else {
      systemObjection = `${qty} units leaves available stock at ${availableAfter}, which is below the derived reorder point of ${reorderPoint}. At ${dailyDemand} units/day this SKU remains in breach immediately. Recommended quantity remains ${recommendedQty}.`;
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    onConfirm({
      quantity: qty,
      modified_quantity: qty,
      modified_supplier_id: selectedSupplierId,
      rationale: rationale.trim() || undefined,
      system_objection: systemObjection,
    });
  };

  return (
    <Card
      title="COUNTER-PROPOSAL & LIVE RECOMPUTATION"
      style={{
        marginBottom: '1.25rem',
        border: '2px solid var(--accent)',
        background: 'var(--surface-0)',
      }}
    >
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: 'var(--t-meta-size)', fontWeight: 600, color: 'var(--ink-1)', marginBottom: '0.35rem' }}>
              Order Quantity (Units):
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="t-mono" style={{ color: 'var(--ink-3)', fontSize: 'var(--t-meta-size)' }}>
                {recommendedQty} →
              </span>
              <input
                type="number"
                min={1}
                max={10000}
                className="form-control"
                value={counterQty}
                onChange={(e) => setCounterQty(e.target.value)}
                style={{
                  width: '120px',
                  fontFamily: 'var(--font-mono, monospace)',
                  fontWeight: 600,
                  fontSize: '1rem',
                }}
                disabled={isSubmitting}
              />
              <span style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-2)' }}>units</span>
            </div>
          </div>

          {suppliers.length > 1 && (
            <div>
              <label style={{ display: 'block', fontSize: 'var(--t-meta-size)', fontWeight: 600, color: 'var(--ink-1)', marginBottom: '0.35rem' }}>
                Supplier Selection:
              </label>
              <select
                className="form-control"
                value={selectedSupplierId}
                onChange={(e) => setSelectedSupplierId(Number(e.target.value))}
                style={{ width: '100%' }}
                disabled={isSubmitting}
              >
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} (₹{s.unit_price} · {s.lead_time_days}d lead)
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Live Recomputed Metrics Box */}
        <div
          style={{
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            padding: '1rem',
            marginBottom: '1rem',
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 'var(--t-meta-size)', color: 'var(--ink-1)', marginBottom: '0.65rem' }}>
            ⟳ LIVE RECOMPUTED IMPACT
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
            <div>
              <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>Order Value</div>
              <div className="t-mono" style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ink-1)' }}>
                ₹{orderValue.toLocaleString('en-IN')}
              </div>
              <div style={{ fontSize: '11px', color: isBelowThreshold ? 'var(--good)' : 'var(--warn)' }}>
                {isBelowThreshold ? '✓ Within agent threshold (≤ ₹50,000)' : '⚠ Above ₹50,000 limit'}
              </div>
            </div>

            <div>
              <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>Available Stock After</div>
              <div className="t-mono" style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ink-1)' }}>
                {availableAfter} units
              </div>
              <div style={{ fontSize: '11px', color: 'var(--ink-2)' }}>
                ROP target: {reorderPoint} units ({marginAboveRop >= 0 ? `+${marginAboveRop}` : marginAboveRop})
              </div>
            </div>

            <div>
              <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>Coverage Horizon</div>
              <div className="t-mono" style={{ fontSize: '1.05rem', fontWeight: 700, color: isUnderRecommended ? 'var(--warn)' : 'var(--good)' }}>
                {coverDays.toFixed(1)} days
              </div>
              <div style={{ fontSize: '11px', color: 'var(--ink-2)' }}>
                Against {leadTimeDays}-day supplier lead time
              </div>
            </div>
          </div>

          {/* CRITICAL INVARIANT: System Objection visible BEFORE override */}
          {systemObjection && (
            <div
              style={{
                marginTop: '0.85rem',
                padding: '0.75rem 0.9rem',
                background: 'rgba(217, 119, 6, 0.08)',
                borderLeft: '3px solid var(--warn)',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 'var(--t-meta-size)', color: 'var(--warn)', marginBottom: '0.25rem' }}>
                ▲ SYSTEM OBJECTION (Visible before confirmation):
              </div>
              <p style={{ margin: 0, fontSize: 'var(--t-body-size)', color: 'var(--ink-1)', lineHeight: 1.5 }}>
                {systemObjection}
              </p>
              <div style={{ fontSize: '11px', color: 'var(--ink-3)', marginTop: '0.35rem' }}>
                ⓘ Proceeding will permanently log this counter-proposal alongside the system objection in the decision ledger.
              </div>
            </div>
          )}
        </div>

        {/* Manager note / rationale */}
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', fontSize: 'var(--t-meta-size)', fontWeight: 600, color: 'var(--ink-1)', marginBottom: '0.35rem' }}>
            Manager Override Note (Optional):
          </label>
          <input
            type="text"
            className="form-control"
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            placeholder="e.g. Budget constrained until month-end, secondary supplier expediting available..."
            style={{ width: '100%', boxSizing: 'border-box' }}
            disabled={isSubmitting}
          />
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Keep {recommendedQty} units / Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting || qty <= 0}
            style={{ fontWeight: 600 }}
          >
            {isSubmitting
              ? 'Submitting Override...'
              : `Approve ${qty} units anyway`}
          </button>
        </div>
      </form>
    </Card>
  );
}

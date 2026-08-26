import React from 'react';

/**
 * 15-SHARED-CONTRACTS.md §13.1 & §14 MetricTile Primitive
 * Tier: T1 (Direct/Ledger), T2 (Computed/Simulated), T3 (Gaps/Missing Input)
 * Hard rule: T3 metric displays formula & missing input, NEVER an invented figure!
 */
export default function MetricTile({
  label,
  value,
  tier = 'T1',
  disclosure = 'synthetic',
  formula,
  missingInput,
  prefix = '',
  suffix = '',
  isLead = false,
  detail,
  className = '',
}) {
  const isT3 = tier === 'T3' || value === null || value === undefined;

  return (
    <div
      className={`metric-tile ${isLead ? 'metric-lead' : ''} ${className}`}
      style={{
        background: 'var(--surface-0)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: isLead ? '1.5rem' : '1.15rem 1.25rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
        <span style={{
          fontSize: 'var(--t-meta-size)',
          fontWeight: 600,
          color: 'var(--ink-2)',
          textTransform: 'uppercase',
          letterSpacing: '0.03em',
        }}>
          {label}
        </span>
        <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '0.1rem 0.35rem',
              borderRadius: 'var(--radius-sm)',
              background: tier === 'T3' ? 'rgba(181, 71, 8, 0.1)' : 'var(--surface-2)',
              color: tier === 'T3' ? 'var(--warn)' : 'var(--ink-2)',
            }}
          >
            {tier}
          </span>
          {disclosure && (
            <span
              style={{
                fontSize: '10px',
                color: 'var(--ink-3)',
                fontStyle: 'italic',
              }}
            >
              {disclosure}
            </span>
          )}
        </div>
      </div>

      {isT3 ? (
        <div style={{ margin: '0.5rem 0' }}>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginBottom: '0.2rem' }}>
            What we cannot measure yet
          </div>
          {missingInput && (
            <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--critical)', fontWeight: 500 }}>
              Needs: {missingInput}
            </div>
          )}
          {formula && (
            <div className="t-mono" style={{ fontSize: '11px', color: 'var(--ink-2)', marginTop: '0.25rem' }}>
              {formula}
            </div>
          )}
        </div>
      ) : (
        <div style={{ margin: '0.5rem 0' }}>
          <span
            className="t-mono"
            style={{
              fontSize: isLead ? 'var(--t-display-size)' : '1.65rem',
              lineHeight: 1.2,
              fontWeight: 700,
              color: 'var(--ink-1)',
            }}
          >
            {prefix}{typeof value === 'number' ? value.toLocaleString('en-IN') : value}{suffix}
          </span>
        </div>
      )}

      {detail && (
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginTop: '0.35rem' }}>
          {detail}
        </div>
      )}
    </div>
  );
}

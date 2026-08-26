import React from 'react';

/**
 * 15-SHARED-CONTRACTS.md §13.1 RefusalCard Primitive
 * A refusal is a legitimate result with its own first-class rendering, not an error banner.
 * Shows what was needed, what was available, the policy/manual citation, and recommendations.
 */
export default function RefusalCard({
  title = 'Declined — Insufficient Data',
  needed,
  have,
  suggestion,
  citation,
  className = '',
}) {
  return (
    <div
      className={`refusal-card ${className}`}
      style={{
        background: 'var(--surface-0)',
        border: '1px solid var(--border)',
        borderLeft: '4px solid var(--warn)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem 1.5rem',
        margin: '1rem 0',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <span style={{ color: 'var(--warn)', fontWeight: 700, fontSize: '1.1rem' }}>⚠</span>
        <h4 style={{
          fontSize: 'var(--t-heading-size)',
          lineHeight: 'var(--t-heading-line)',
          fontWeight: 600,
          color: 'var(--ink-1)',
          margin: 0,
        }}>
          {title}
        </h4>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '1rem',
        background: 'var(--surface-1)',
        padding: '0.85rem 1rem',
        borderRadius: 'var(--radius-sm)',
        marginBottom: '0.75rem',
      }}>
        <div>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', fontWeight: 600, marginBottom: '0.2rem' }}>
            WHAT WAS NEEDED
          </div>
          <div className="t-mono" style={{ fontSize: 'var(--t-mono-size)', color: 'var(--ink-1)', fontWeight: 500 }}>
            {needed || 'Sufficient historical sales'}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', fontWeight: 600, marginBottom: '0.2rem' }}>
            WHAT WAS AVAILABLE
          </div>
          <div className="t-mono" style={{ fontSize: 'var(--t-mono-size)', color: 'var(--critical)', fontWeight: 600 }}>
            {have || '0 records'}
          </div>
        </div>
      </div>

      {suggestion && (
        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)', marginBottom: '0.5rem' }}>
          <strong>Next steps:</strong> {suggestion}
        </p>
      )}

      {citation && (
        <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>
          Governed by: <strong>{citation}</strong>
        </div>
      )}
    </div>
  );
}

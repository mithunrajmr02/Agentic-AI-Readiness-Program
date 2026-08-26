import React from 'react';
import ProvenanceMark from './ProvenanceMark';

/**
 * 15-SHARED-CONTRACTS.md §13.1 EvidenceBlock Primitive
 * Renders the arithmetic breakdown, formula citation, inputs, and final result.
 */
export default function EvidenceBlock({
  inputs = {},
  formula,
  citation,
  result,
  title = 'WHY THIS FIRED',
  className = '',
}) {
  const inputEntries = typeof inputs === 'object' && inputs !== null ? Object.entries(inputs) : [];

  return (
    <div
      className={`evidence-block ${className}`}
      style={{
        background: 'var(--surface-1)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem',
        marginTop: '0.75rem',
        marginBottom: '0.75rem',
      }}
    >
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.75rem',
        borderBottom: '1px solid var(--border)',
        paddingBottom: '0.5rem',
      }}>
        <span style={{
          fontSize: 'var(--t-meta-size)',
          fontWeight: 700,
          color: 'var(--ink-2)',
          letterSpacing: '0.04em',
        }}>
          {title}
        </span>
        <ProvenanceMark kind="computed" citation={citation} />
      </div>

      {/* Input Breakdown Table */}
      {inputEntries.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '0.75rem' }}>
          {inputEntries.map(([k, v]) => (
            <div key={k} style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: 'var(--t-body-size)',
            }}>
              <span style={{ color: 'var(--ink-2)', textTransform: 'capitalize' }}>
                {k.replace(/_/g, ' ')}
              </span>
              <span className="t-mono" style={{ fontWeight: 600, color: 'var(--ink-1)' }}>
                {typeof v === 'number' ? v.toLocaleString('en-IN') : String(v)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Formula & Calculation */}
      {formula && (
        <div style={{
          background: 'var(--surface-0)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.65rem 0.85rem',
          marginBottom: '0.75rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginBottom: '0.2rem' }}>Formula</div>
            <div className="t-mono" style={{ fontSize: 'var(--t-mono-size)', color: 'var(--ink-1)' }}>
              {formula}
            </div>
          </div>
          {result !== undefined && result !== null && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)', marginBottom: '0.2rem' }}>Result</div>
              <div className="t-mono" style={{ fontSize: 'var(--t-mono-size)', fontWeight: 700, color: 'var(--accent)' }}>
                {typeof result === 'number' ? result.toLocaleString('en-IN') : String(result)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Citation Link */}
      {citation && (
        <div style={{
          fontSize: 'var(--t-meta-size)',
          color: 'var(--ink-3)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
        }}>
          <span>ⓘ</span>
          <span>Citation: <strong>{citation}</strong></span>
        </div>
      )}
    </div>
  );
}

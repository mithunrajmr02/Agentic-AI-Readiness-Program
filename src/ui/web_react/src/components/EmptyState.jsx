import React from 'react';

/**
 * 15-SHARED-CONTRACTS.md §13.1 EmptyState Primitive
 * Renders reason, formula, missing inputs, and potential action.
 */
export default function EmptyState({
  title = 'No Data Available',
  reason,
  formula,
  missingInput,
  action,
  icon = '○',
  className = '',
}) {
  return (
    <div
      className={`empty-state-primitive ${className}`}
      style={{
        textAlign: 'center',
        padding: '2.5rem 1.5rem',
        background: 'var(--surface-0)',
        border: '1px dashed var(--border)',
        borderRadius: 'var(--radius-md)',
        color: 'var(--ink-2)',
      }}
    >
      <div style={{
        fontSize: '2rem',
        color: 'var(--ink-3)',
        marginBottom: '0.75rem',
      }}>
        {icon}
      </div>

      <h4 style={{
        fontSize: 'var(--t-heading-size)',
        fontWeight: 600,
        color: 'var(--ink-1)',
        marginBottom: '0.5rem',
      }}>
        {title}
      </h4>

      {reason && (
        <p style={{
          fontSize: 'var(--t-body-size)',
          color: 'var(--ink-2)',
          maxWidth: '480px',
          margin: '0 auto 1rem auto',
        }}>
          {reason}
        </p>
      )}

      {(formula || missingInput) && (
        <div style={{
          display: 'inline-block',
          textAlign: 'left',
          background: 'var(--surface-1)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.75rem 1rem',
          margin: '0.5rem auto 1rem auto',
          maxWidth: '520px',
        }}>
          {formula && (
            <div style={{ marginBottom: missingInput ? '0.4rem' : 0 }}>
              <span style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-3)' }}>Formula: </span>
              <span className="t-mono" style={{ fontSize: 'var(--t-mono-size)', color: 'var(--ink-1)' }}>{formula}</span>
            </div>
          )}
          {missingInput && (
            <div>
              <span style={{ fontSize: 'var(--t-meta-size)', color: 'var(--critical)' }}>Missing input: </span>
              <span style={{ fontSize: 'var(--t-meta-size)', color: 'var(--ink-1)' }}>{missingInput}</span>
            </div>
          )}
        </div>
      )}

      {action && (
        <div style={{ marginTop: '1rem' }}>
          {action}
        </div>
      )}
    </div>
  );
}

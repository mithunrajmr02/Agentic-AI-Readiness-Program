import React from 'react';

/**
 * 15-SHARED-CONTRACTS.md §13.1 & 07-UX-ARCHITECTURE.md §5.3 ThreeDoorPanel Primitive
 * CRITICAL INVARIANT:
 * Approve, Reject, and Counter MUST have IDENTICAL visual weight.
 * No prominent primary button bias — an approval surface must not manufacture consent.
 */
export default function ThreeDoorPanel({
  onApprove,
  onReject,
  onCounter,
  disabled = false,
  approveLabel = 'Approve',
  rejectLabel = 'Reject…',
  counterLabel = 'Change quantity or supplier…',
  className = '',
}) {
  const doorBtnStyle = {
    flex: 1,
    padding: '0.85rem 1.25rem',
    background: 'var(--surface-0)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--ink-1)',
    fontSize: 'var(--t-body-size)',
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1,
    textAlign: 'center',
    transition: 'background-color 0.15s ease, border-color 0.15s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '48px',
  };

  return (
    <div
      className={`three-door-panel ${className}`}
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1.2fr',
        gap: '1rem',
        marginTop: '1.5rem',
        marginBottom: '1rem',
      }}
    >
      <button
        type="button"
        style={doorBtnStyle}
        onClick={onApprove}
        disabled={disabled}
        className="door-btn door-approve"
      >
        {approveLabel}
      </button>

      <button
        type="button"
        style={doorBtnStyle}
        onClick={onReject}
        disabled={disabled}
        className="door-btn door-reject"
      >
        {rejectLabel}
      </button>

      <button
        type="button"
        style={doorBtnStyle}
        onClick={onCounter}
        disabled={disabled}
        className="door-btn door-counter"
      >
        {counterLabel}
      </button>
    </div>
  );
}

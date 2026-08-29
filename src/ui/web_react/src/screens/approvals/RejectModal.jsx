import React, { useState } from 'react';

/**
 * 15-SHARED-CONTRACTS.md §8 & 07-UX-ARCHITECTURE.md §5.3
 * Reject modal requiring mandatory rationale for audit training and calibration.
 */
export default function RejectModal({
  isOpen,
  onClose,
  onConfirm,
  isSubmitting = false,
}) {
  const [rationale, setRationale] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!rationale.trim()) {
      setError('Rejection rationale is required by governance policy (audit requirement).');
      return;
    }
    setError('');
    onConfirm(rationale.trim());
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        backgroundColor: 'var(--surface-0)',
        borderRadius: 'var(--radius-md)',
        maxWidth: '520px',
        width: '90%',
        padding: '1.5rem',
        boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
        border: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600, color: 'var(--ink-1)' }}>
            Reject Proposal
          </h3>
          <button
            type="button"
            onClick={onClose}
            style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--ink-3)' }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: 'var(--t-body-size)', color: 'var(--ink-2)', marginBottom: '1rem', lineHeight: 1.5 }}>
          Please provide the reason for rejecting this replenishment proposal. Rejection rationales are recorded in the immutable ledger and used to calibrate future recommendations.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: 'var(--t-meta-size)', fontWeight: 600, color: 'var(--ink-1)', marginBottom: '0.4rem' }}>
              Rejection Rationale <span style={{ color: 'var(--critical)' }}>*</span>
            </label>
            <textarea
              className="form-control"
              rows={3}
              value={rationale}
              onChange={(e) => {
                setRationale(e.target.value);
                if (error) setError('');
              }}
              placeholder="e.g. Existing stock discovered in back room, or supplier lead time acceptable for delay..."
              style={{
                width: '100%',
                padding: '0.65rem',
                borderRadius: 'var(--radius-sm)',
                border: error ? '1px solid var(--critical)' : '1px solid var(--border)',
                fontFamily: 'inherit',
                fontSize: 'var(--t-body-size)',
                boxSizing: 'border-box',
              }}
              disabled={isSubmitting}
            />
            {error && (
              <div style={{ color: 'var(--critical)', fontSize: 'var(--t-meta-size)', marginTop: '0.35rem' }}>
                {error}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button
              type="button"
              className="btn btn-outline"
              onClick={onClose}
              disabled={isSubmitting}
              style={{ padding: '0.5rem 1rem' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn"
              disabled={isSubmitting}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: 'var(--critical)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontWeight: 600,
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
              }}
            >
              {isSubmitting ? 'Recording Rejection...' : 'Confirm Rejection'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

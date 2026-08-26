import React from 'react';

/**
 * 15-SHARED-CONTRACTS.md §13.1 & 07-UX-ARCHITECTURE.md §7.1 ProvenanceMark Primitive
 * Three primary marks: computed | retrieved | generated + human (@)
 * Visual boundary between deterministic calculation and LLM narrative.
 */
export default function ProvenanceMark({
  kind = 'computed',
  citation,
  user,
  timestamp,
  children,
  className = '',
}) {
  const normKind = String(kind || 'computed').toLowerCase();

  if (normKind === 'generated') {
    return (
      <span
        className={`provenance-mark provenance-generated ${className}`}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.35rem',
          color: 'var(--agent)',
          backgroundColor: 'rgba(91, 33, 182, 0.08)',
          border: '1px solid rgba(91, 33, 182, 0.25)',
          padding: '0.1rem 0.45rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: 'var(--t-meta-size)',
          fontWeight: 600,
        }}
        title="Agent-generated narrative"
      >
        <span aria-hidden="true">◈</span>
        <span>{children || 'agent'}</span>
      </span>
    );
  }

  if (normKind === 'retrieved') {
    return (
      <span
        className={`provenance-mark provenance-retrieved ${className}`}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.3rem',
          color: 'var(--ink-2)',
          fontSize: 'var(--t-meta-size)',
          fontStyle: 'italic',
        }}
        title={citation ? `Retrieved: ${citation}` : 'Retrieved from records'}
      >
        <span aria-hidden="true">⌕</span>
        <span>{children || (citation ? `retrieved (${citation})` : 'retrieved')}</span>
      </span>
    );
  }

  if (normKind === 'human' || normKind === 'user') {
    return (
      <span
        className={`provenance-mark provenance-human ${className}`}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.3rem',
          color: 'var(--ink-1)',
          fontSize: 'var(--t-meta-size)',
          fontWeight: 500,
        }}
        title={`Decided by human: ${user || 'operator'}${timestamp ? ` at ${timestamp}` : ''}`}
      >
        <span aria-hidden="true" style={{ color: 'var(--accent)' }}>@</span>
        <span>{children || user || 'human'}</span>
      </span>
    );
  }

  // Default: computed (normal ink with optional citation tooltip)
  return (
    <span
      className={`provenance-mark provenance-computed ${className}`}
      style={{
        color: 'inherit',
      }}
      title={citation ? `Computed from ledger: ${citation}` : 'Computed deterministically from ledger'}
    >
      {children}
    </span>
  );
}

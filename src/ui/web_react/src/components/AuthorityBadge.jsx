import React from 'react';

/**
 * 15-SHARED-CONTRACTS.md §13.1 AuthorityBadge Primitive
 * Autonomy modes: "off" | "shadow" | "assisted" | "autonomous"
 */
export default function AuthorityBadge({ mode = 'assisted', className = '' }) {
  const norm = String(mode || 'assisted').toLowerCase();

  let label = 'Assisted';
  let color = 'var(--accent)';
  let bg = 'rgba(26, 86, 219, 0.1)';
  let border = 'rgba(26, 86, 219, 0.3)';

  if (norm === 'autonomous') {
    label = 'Autonomous';
    color = 'var(--good)';
    bg = 'rgba(5, 96, 58, 0.1)';
    border = 'rgba(5, 96, 58, 0.3)';
  } else if (norm === 'shadow') {
    label = 'Shadow';
    color = 'var(--warn)';
    bg = 'rgba(181, 71, 8, 0.1)';
    border = 'rgba(181, 71, 8, 0.3)';
  } else if (norm === 'off') {
    label = 'Manual / Off';
    color = 'var(--critical)';
    bg = 'rgba(196, 38, 46, 0.1)';
    border = 'rgba(196, 38, 46, 0.3)';
  }

  return (
    <span
      className={`authority-badge ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        padding: '0.2rem 0.6rem',
        borderRadius: 'var(--radius-full)',
        fontSize: 'var(--t-meta-size)',
        lineHeight: 'var(--t-meta-line)',
        fontWeight: 600,
        color: color,
        backgroundColor: bg,
        border: `1px solid ${border}`,
      }}
      title={`Autonomy Mode: ${label}`}
    >
      <span aria-hidden="true" style={{ fontSize: '0.65rem' }}>●</span>
      <span>mode: {label.toLowerCase()}</span>
    </span>
  );
}

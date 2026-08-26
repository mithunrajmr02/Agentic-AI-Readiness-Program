import React from 'react';

/**
 * 15-SHARED-CONTRACTS.md §13.1 SeverityDot Primitive
 * Absolute requirement: NEVER encode severity in colour alone.
 * Must carry Shape symbol (▲, ●, ○, ✓) + text label for accessibility.
 */
export default function SeverityDot({ severity, label, showLabel = true }) {
  const norm = String(severity || 'info').toLowerCase();

  let shape = '○';
  let defaultLabel = 'Info';
  let color = 'var(--ink-2)';
  let bg = 'var(--surface-2)';

  if (norm === 'critical') {
    shape = '▲';
    defaultLabel = 'Critical';
    color = 'var(--critical)';
    bg = 'rgba(196, 38, 46, 0.12)';
  } else if (norm === 'warn' || norm === 'warning' || norm === 'high') {
    shape = '●';
    defaultLabel = norm === 'high' ? 'High' : 'Warning';
    color = 'var(--warn)';
    bg = 'rgba(181, 71, 8, 0.12)';
  } else if (norm === 'medium') {
    shape = '●';
    defaultLabel = 'Medium';
    color = 'var(--warn)';
    bg = 'rgba(181, 71, 8, 0.08)';
  } else if (norm === 'low' || norm === 'info') {
    shape = '○';
    defaultLabel = norm === 'low' ? 'Low' : 'Info';
    color = 'var(--ink-2)';
    bg = 'var(--surface-2)';
  } else if (norm === 'good' || norm === 'resolved' || norm === 'success') {
    shape = '✓';
    defaultLabel = norm === 'resolved' ? 'Resolved' : 'Healthy';
    color = 'var(--good)';
    bg = 'rgba(5, 96, 58, 0.12)';
  }

  const textLabel = label || defaultLabel;

  return (
    <span
      className="severity-dot"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        padding: '0.15rem 0.5rem',
        borderRadius: 'var(--radius-full)',
        fontSize: 'var(--t-meta-size)',
        lineHeight: 'var(--t-meta-line)',
        fontWeight: 600,
        color: color,
        backgroundColor: bg,
      }}
      title={`${textLabel} severity`}
    >
      <span aria-hidden="true" style={{ fontSize: '0.75rem' }}>{shape}</span>
      {showLabel && <span>{textLabel}</span>}
    </span>
  );
}

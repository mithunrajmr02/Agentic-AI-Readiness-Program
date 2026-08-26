import React from 'react';

/**
 * 15-SHARED-CONTRACTS.md §13.1 Card Primitive
 * Supports two elevation levels per 07-UX-ARCHITECTURE §4.4:
 * Flat (surface-1 panel with 1px border) and Raised (modals/drawers with shadow).
 */
export default function Card({
  title,
  subtitle,
  elevation = 'flat',
  actions,
  children,
  className = '',
  style = {},
}) {
  const isRaised = elevation === 'raised' || elevation === 2;

  const cardStyle = {
    background: 'var(--surface-0)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    padding: '1.25rem 1.5rem',
    boxShadow: isRaised ? 'var(--shadow-overlay)' : 'none',
    ...style,
  };

  return (
    <div className={`card-primitive ${className}`} style={cardStyle}>
      {(title || actions || subtitle) && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: children ? '1rem' : 0,
          gap: '1rem',
        }}>
          <div>
            {title && (
              <h3 style={{
                fontSize: 'var(--t-heading-size)',
                lineHeight: 'var(--t-heading-line)',
                fontWeight: 'var(--t-heading-weight)',
                color: 'var(--ink-1)',
                margin: 0,
              }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <p style={{
                fontSize: 'var(--t-meta-size)',
                color: 'var(--ink-3)',
                marginTop: '0.25rem',
                marginBotom: 0,
              }}>
                {subtitle}
              </p>
            )}
          </div>
          {actions && (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              {actions}
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  );
}
